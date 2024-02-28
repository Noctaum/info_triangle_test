import requests
import urllib.parse
import tensorflow as tf
import itertools


# test class for help search possible variants
class PlatformResearcher:
    key = ''
    token = ''
    commission = 0.01
    delay = 0.5
    play_value = 1
    loud_list = ['FX']
    # api constants
    api = {
        'api': 'https://api.bitflyer.com/v1/',
        'market_api': 'getmarkets',
        'board_api': 'getboard',
        'ticker_api': 'getticker'
    }
    product_code_name = 'product_code'
    # search_pairs constants
    pair_field_name = 'product_code'

    # collector of counted info
    # should be review after count
    triplets = [{
        'clear_pairs': ['BTC_JPY', 'ETH_JPY', 'ETH_BTC'],
        'triplet': ['BTC', 'ETH', 'JPY']
    }]
    best_variants = []

    def concat_list(self, currency_pair_list):
        new_pair_list = []
        for index_i, currency_pair_i in enumerate(currency_pair_list):
            for index_j, currency_pair_j in enumerate(currency_pair_list):
                if index_j > index_i:
                    test_array = list({*currency_pair_j, *currency_pair_i})
                    # if we get len = 2 it means that we get pair that not useful for triangle
                    if len(test_array) == 3:
                        new_pair_list.append(test_array)

        return new_pair_list

    def search_pairs(self):
        try:
            pair_info = self.request_info(self.api.get('market_api'))
            # need for future count
            currency_list_clear = [pair.get(self.product_code_name, '') for pair in pair_info if not any([el in pair.get(self.product_code_name, '') for el in self.loud_list])]
            currency_list = [pair.split('_') for pair in currency_list_clear]
            all_currency = list(itertools.chain.from_iterable(currency_list))
            count_currency = {i: all_currency.count(i) for i in all_currency}
            new_currency_pair = []
            for currency_pair in currency_list:
                if all([count_currency[i] > 1 for i in currency_pair]):
                    new_currency_pair.append(currency_pair)
            # create doublet
            double_pair = self.concat_list(new_currency_pair)
            # create triplet
            double_pair = self.concat_list(double_pair)
            # sort
            double_pair = [sorted(triplet) for triplet in double_pair]
            # remove duplicated
            ready_lists = []
            for triplet in double_pair:
                if triplet not in ready_lists:
                    ready_lists.append(triplet)

            clear_pairs_array = []
            for ready_triplet in ready_lists:
                new_clear_pair_triplet = []
                for clear_pair in currency_list_clear:
                    counter = 0
                    for triplet in ready_triplet:
                        if triplet in clear_pair:
                            counter = counter + 1
                    if counter == 2:
                        new_clear_pair_triplet.append(clear_pair)
                clear_pairs_array.append({
                    'clear_pairs': new_clear_pair_triplet,
                    'triplet': ready_triplet
                })

            self.triplets = clear_pairs_array
        except Exception as exc:
            # TODO log errors
            error_message = f"{type(exc).__name__} {exc.args}"
            print(error_message)

    def request_info(self, request='', params={}):
        try:
            url = urllib.parse.urljoin(self.api.get('api'), request)
            response = requests.get(url, params=params)
            response_json = response.json()
            return response_json
        except Exception as exc:
            error_message = f"{type(exc).__name__} {exc.args}"
            raise Exception(error_message)

    def collect_triplet_variant(self, triplet):
        variant_alpha = triplet
        variant_alpha_rev = variant_alpha[::-1]
        variant_beta = variant_alpha[-1:] + variant_alpha[:-1]
        variant_beta_rev = variant_beta[::-1]
        variant_gamma = variant_beta[-1:] + variant_beta[:-1]
        variant_gamma_rev = variant_gamma[::-1]

        alphabet_list = [
            variant_alpha,
            variant_alpha_rev,
            variant_beta,
            variant_beta_rev,
            variant_gamma,
            variant_gamma_rev
        ]

        return alphabet_list

    def count_diff(self, triplet):
        try:
            variant_list = self.collect_triplet_variant(triplet.get('triplet'))

            result_array = []
            for pair in triplet.get('clear_pairs'):
                currency_info = self.request_info(self.api.get('ticker_api'), params={self.product_code_name: pair})

                result_array.append({
                    'type': pair,
                    'buy': currency_info.get('best_ask'),
                    'sell': currency_info.get('best_bid'),
                    'ltp': currency_info.get('ltp'),
                })

            best_variant = None
            best_value = 0
            for variant in variant_list:
                alfa_beta_trans = None
                beta_gamma_trans = None
                gamma_alfa_trans = None

                for result in result_array:
                    result_type = result.get('type', '')
                    if result_type.startswith(variant[0]) and result_type.endswith(variant[1]):
                        alfa_beta_trans = result.get('ltp')
                    elif result_type.startswith(variant[0]) and result_type.endswith(variant[2]):
                        gamma_alfa_trans = 1 / result.get('ltp')
                    elif result_type.startswith(variant[1]) and result_type.endswith(variant[0]):
                        alfa_beta_trans = 1 / result.get('ltp')
                    elif result_type.startswith(variant[1]) and result_type.endswith(variant[2]):
                        beta_gamma_trans = result.get('ltp')
                    elif result_type.startswith(variant[2]) and result_type.endswith(variant[0]):
                        gamma_alfa_trans = result.get('ltp')
                    elif result_type.startswith(variant[2]) and result_type.endswith(variant[1]):
                        beta_gamma_trans = 1 / result.get('ltp')
                    else:
                        message = 'Issue in count_diff_by_best'
                        print(message)
                        raise Exception(message)

                result_value = self.play_value * alfa_beta_trans * beta_gamma_trans * gamma_alfa_trans
                if result_value > self.play_value and result_value > best_value:
                    best_value = result_value
                    best_variant = variant

            if best_variant:
                print(f'investigation result: {best_variant}, {best_value}')
                self.best_variants.append({
                    'variant': best_variant,
                    'value': best_value,
                    'triplet': triplet,
                })

        except Exception as exc:
            # TODO log errors
            error_message = f"{type(exc).__name__} {exc.args}"
            print(error_message)

    def count_all_diff(self):
        for triplet in self.triplets:
            self.count_diff(triplet)

    def run(self):
        self.search_pairs()
        self.count_all_diff()
        print(self.best_variants)
