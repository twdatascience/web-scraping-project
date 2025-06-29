import utils.helpers as helpers
import os
import datetime

# Check if today's data is already in web_data
today_str = datetime.date.today().isoformat()
web_data_dir = "./web_data"
expected_files = [
    f"{today_str}_soprisselfstorage.html",
    f"{today_str}_storquestselfstorage.html",
    f"{today_str}_storage_mart.html",
    f"{today_str}_all_hours.html",
    f"{today_str}_carbondale.html",
    f"{today_str}_basaltmini_cc.html",
    f"{today_str}_basaltmini_reg.html"
]
all_exist = all(os.path.exists(os.path.join(web_data_dir, fname)) for fname in expected_files)

if all_exist:
    print("Today's data already exists in web_data. Syncing to database if needed...")
    helpers.sync_web_data_to_db(db_path="storage_data.db", web_data_dir=web_data_dir)
else:
    helpers.sync_web_data_to_db(db_path="storage_data.db", web_data_dir=web_data_dir)
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

    basalt_cc = 'https://www.spacecontroletrans.com/scStarOnlinePayment/index.html?CompanyId=327-SF&ConnectionType=Connection#/displaySizes'
    basalt_reg = 'https://www.spacecontroletrans.com/scStarOnlinePayment/index.html?CompanyId=327-BS&ConnectionType=Connection#/displaySizes'
    basalt_soup1, basalt_soup2 = helpers.fetch_basalt_mini(basalt_cc, basalt_reg)


    sopris_results = helpers.extract_sopris(sopris_soup)
    if not sopris_results or len(sopris_results) == 0:
        sopris_results = {0: ("Something went wrong", "Contact Tyler Wilson", "")}

    storquest_results = helpers.extract_storquest(storquest_soup)
    if not storquest_results or len(storquest_results) == 0:
        storquest_results = {0: ("Something went wrong", "Contact Tyler Wilson", "")}

    storage_mart_results = helpers.extract_storage_mart(storage_mart_soup)
    if not storage_mart_results or len(storage_mart_results) == 0:
        storage_mart_results = {0: ("Something went wrong", "Contact Tyler Wilson", "")}

    all_hours_results = helpers.extract_all_hours(all_hours_soup)
    if not all_hours_results or len(all_hours_results) == 0:
        all_hours_results = {0: ("Something went wrong", "Contact Tyler Wilson", "")}

    carbondale_results = helpers.extract_carbondale(carbondale_soup)
    if not carbondale_results or len(carbondale_results) == 0:
        carbondale_results = {0: ("Something went wrong", "Contact Tyler Wilson", "")}
    
    basalt_results = helpers.extract_basalt(basalt_soup1, basalt_soup2)
    if not basalt_results or len(basalt_results) == 0:
        basalt_results = {0: ("Something went wrong", "Contact Tyler Wilson", "")}

    combined_results = helpers.combine_all_results(
        sopris_results, storquest_results, storage_mart_results,
        all_hours_results, carbondale_results, basalt_results
    )

    helpers.create_db_and_table()
    helpers.insert_combined_results(combined_results)
    helpers.write_multiple_results_to_excel(
        sopris_results, storquest_results, storage_mart_results,
        all_hours_results, carbondale_results, basalt_results
    )
