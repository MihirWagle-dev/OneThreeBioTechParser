import flask
import requests
from flask import jsonify
from bs4 import BeautifulSoup
import csv


class OneThreeBioTech:
    def __init__(self):
        self.target_genes = {}
        self.incomplete_urls = []

    # this method can be used to read the input from a csv file
    def read_ids(self):
        try:
            with open('ids_of_interest.csv') as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=',')
                input_ids = []
                for row in csv_reader:
                    input_ids = row
                return input_ids
        except FileNotFoundError:
            print("Could not read the ids_of_interest.csv file")
            exit(1)

    def number_of_targets(self, soup):
        target_number_str = soup.find_all("a", attrs={"class": "btn bond-link targets"})
        target_number = str(target_number_str)
        start = target_number.find("(")
        end = target_number.find(")")
        return target_number[start + 1:end]

    def extract_genes(self, number, bond_list_str):
        targets = []
        while int(number) > 0:
            start = bond_list_str.find("Gene Name")
            end = bond_list_str.find("</dd>", start)
            gene_name = bond_list_str[start:end]
            start_sub = gene_name.rfind(">")
            targets.append(gene_name[start_sub+1:])
            bond_list_str = bond_list_str[end:len(bond_list_str)]
            number = int(number) - 1
        return targets

    # this method can be used to write to a csv file
    def write_to_file(self):
        with open('target_genes.csv', mode='w') as target_genes_file:
            writer = csv.writer(target_genes_file)
            writer.writerows(self.target_genes.items())
            writer.writerow(["Incomplete urls are as follows:"])
            writer.writerow(self.incomplete_urls)

    def process_inputs(self, ids):
        ids_of_interest = list(ids.split(","))
        for id in ids_of_interest:
            URL = 'https://www.drugbank.ca/drugs/' + str(id)
            page = requests.get(URL)
            soup = BeautifulSoup(page.content, 'lxml')
            number = self.number_of_targets(soup)

            # skip the url if the number of targets is not clearly defined
            if number.isnumeric() is False:
                self.incomplete_urls.append(URL)
                continue

            bond_list = soup.find_all("div", attrs={"class": "bond-list-container targets"})
            bond_list_str = str(bond_list)
            self.target_genes[URL] = self.extract_genes(number, bond_list_str)
            # uncomment the below line if you wish to write to a csv file in the current directory
            # self.write_to_file()



app = flask.Flask(__name__)
app.config["DEBUG"] = True


@app.route('/TargetGenes/<ids>', methods=['GET'])
def home(ids):
    print(ids)
    parse = OneThreeBioTech()
    parse.process_inputs(ids)
    return jsonify(parse.target_genes)

app.run()