""" 
Required Packages to be installed
!pip install streamlit
!pip install beautifulsoup4==4.12.3
!pip install requests
!pip install pandas

"""



import requests
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st

def scrape_arxiv_pagination(url):
    """Gets the pagination links from the specified URL."""
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to retrieve data: {response.status_code}")
        return {}

    soup = BeautifulSoup(response.content, 'html.parser')
    nav = soup.find('nav', role='navigation')

    if nav:
        ul_element = nav.find('ul', class_='pagination-list')
        if ul_element:
            pagination_links = {}
            for li in ul_element.find_all('li'):
                a_element = li.find('a')
                if a_element:
                    page_number = a_element.text.strip()
                    link = f"https://arxiv.org{a_element['href']}"
                    pagination_links[page_number] = link
            return pagination_links
    return {}

def scrape_research_papers(url):
    """Gets the details of research papers from the specified URL."""
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to retrieve data: {response.status_code}")
        return pd.DataFrame()

    soup = BeautifulSoup(response.content, 'html.parser')
    content_div = soup.select_one('div.content')

    if not content_div:
        print("No content found.")
        return pd.DataFrame()

    ol_element = content_div.find('ol')
    if not ol_element:
        print("No ordered list found.")
        return pd.DataFrame()

    results = []
    for li in ol_element.find_all('li', class_='arxiv-result'):
        pdf_link = li.find('a', href=lambda x: x and 'pdf' in x)
        title = li.find('p', class_='title is-5 mathjax')
        authors = li.find('p', class_='authors')
        submission_info = li.find('p', class_='is-size-7')

        pdf_url = pdf_link['href'] if pdf_link else None
        title_text = title.get_text(strip=True) if title else None

        # Remove "Authors:" prefix and strip whitespace
        authors_text = authors.get_text(strip=True).replace("Authors:", "").strip() if authors else None
        submission_date = submission_info.get_text(strip=True) if submission_info else None

        results.append({
            'Title': title_text,
            'Authors': authors_text,
            'Submission Date': submission_date,
            'PDF Link': f'{pdf_url}' if pdf_url else "N/A"  # Format PDF link for Markdown
        })

    df = pd.DataFrame(results)

    return df

# Streamlit Application
def main():
    st.title("ArXiv Research Papers Scraper")

    query = st.text_input("Enter your search query (e.g., quantum machine learning):")

    num_pages = st.number_input("Number of pages to retrieve:", min_value=1, max_value=5, value=1)

    if st.button("Search"):
        base_url = "https://arxiv.org/search/?query=" + query.replace(" ", "+") + "&searchtype=all"

        # Get pagination links
        pagination_links = scrape_arxiv_pagination(base_url)

        all_results_df = pd.DataFrame()

        # Scrape each page based on user input
        for i in range(num_pages):
            page_url = pagination_links.get(str(i + 1))  # Page numbers start from 1
            if page_url:
                results_df = scrape_research_papers(page_url)
                all_results_df = pd.concat([all_results_df, results_df], ignore_index=True)

        # Display results in Streamlit with clickable PDF links using Markdown
        #st.dataframe(all_results_df.to_markdown(escape=False), unsafe_allow_html=True)
        st.dataframe(
            all_results_df,
            column_config={
                'Title': "Title",
                'Authors': "Authors",
                'Submission Date': 'Submission Date',

                "PDF Link": st.column_config.LinkColumn("PDF Link"),

            },)
        # Download options
        if not all_results_df.empty:
            csv_file = all_results_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download CSV",
                data=csv_file,
                file_name='arxiv_results.csv',
                mime='text/csv',
            )

if __name__ == "__main__":
    main()
