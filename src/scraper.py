import utils.helpers as helpers

# Fetch dynamic content
sopris = 'https://soprisselfstorage.com/rent-storage/'
sopris_soup = helpers.fetch_sopris_self_storage(sopris)

storquest = 'https://www.storquest.com/self-storage/co/carbondale/9160/unit-sizes-prices#/'
storquest_soup = helpers.fetch_storquest_self_storage(storquest)

storage_mart = 'https://www.storage-mart.com/basalt#unitstable'
storage_mart_soup = helpers.fetch_storage_mart(storage_mart)

all_hours = "https://www.aspenbasaltstorage.com/pages/rent"
all_hours_soup = helpers.fetch_all_hours(all_hours)

carbondale = "https://carbondaleministorage.ccstorage.com/find_units"
carbondale_soup = helpers.fetch_carbondale(carbondale)

if __name__ == "__main__":
    sopris_results = helpers.extract_sopris(sopris_soup) 
    storquest_results = helpers.extract_storquest(storquest_soup)
    storage_mart_results = helpers.extract_storage_mart(storage_mart_soup)
    all_hours_results = helpers.extract_all_hours(all_hours_soup)
    carbondale_results = helpers.extract_carbondale(carbondale_soup)
    helpers.write_multiple_results_to_excel(sopris_results, storquest_results, storage_mart_results, all_hours_results, carbondale_results)
