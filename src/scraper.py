from utils.helpers import fetch_sopris_self_storage, extract_sopris, fetch_storquest_self_storage, extract_storquest, fetch_storage_mart, extract_storage_mart, write_multiple_results_to_excel
import pdb

# Fetch dynamic content
sopris = 'https://soprisselfstorage.com/rent-storage/'
sopris_soup = fetch_sopris_self_storage(sopris)

storquest = 'https://www.storquest.com/self-storage/co/carbondale/9160/unit-sizes-prices#/'
storquest_soup = fetch_storquest_self_storage(storquest)

storage_mart = 'https://www.storage-mart.com/basalt#unitstable'
storage_mart_soup = fetch_storage_mart(storage_mart)


if __name__ == "__main__":
    sopris_results = extract_sopris(sopris_soup) 
    storquest_results = extract_storquest(storquest_soup)
    storage_mart_results = extract_storage_mart(storage_mart_soup)
    write_multiple_results_to_excel(sopris_results, storquest_results, storage_mart_results)
