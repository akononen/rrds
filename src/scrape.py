from domainscraper import DepthScraper
import pandas as pd
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--url", type=str, required=True, 
                        help="URL you want to scrape. Remember to define schema e.g. https://")
    parser.add_argument("-sl", "--save_location", type=str, required=True,
                        help="Location of saved file")
    parser.add_argument("-d", "--depth", type=int, required=False, default=1, 
                        help="Depth you want to scrape. 0=only the URL you provide")
    parser.add_argument("-nt", "--no_tags", default=False, action="store_true",
                        help="Set tags placed on personal information off")
    parser.add_argument("-l", "--language", default="eng",
                        choices=["eng", "fin"],
                        help="Set language of the website. English is preferrable.")
    parser.add_argument("-nm", "--ner_model", default="sm", choices=["sm", "lg"],
                        help="Set the model for Named Entity Extraction. Small model has better performance but large has improved accuracy.")

    args = parser.parse_args()

    scraper = DepthScraper(args.url, args.depth, args.no_tags, args.language, args.ner_model)

    scraper.start_scraping()
    data = scraper.get_data()

    df = pd.DataFrame(data)

    df.to_excel(args.save_location)
