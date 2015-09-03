import sys, datetime, re
import requests
from bs4 import BeautifulSoup

FC_RE_URL_STUB = 'http://cas-ncr-nter03.cas-satj.gc.ca/IndexingQueries/infp_RE_info_e.php?court_no='
FC_AI_URL_STUB = 'http://cas-ncr-nter03.cas-satj.gc.ca/IndexingQueries/infp_moreInfo_e.php?'

def fcparse_ai(html):
    """
    Takes HTML text containing electronic docket additional information from
    the Federal Court of Canada and returns a Python dictionary containing the
    parsed information, in key-value pairs.
    """
    # Using html5lib currently due to lack of support for lxml on certain hosts,
    # but lxml can be used as well, and should be equivalent (but faster).
    # Python's default html.parser, however, will not work because it appears
    # to treat each row in a table as a child element of the previous row,
    # which sometimes causes a "maximum recursion depth exceeded" error for
    # long tables
    soup = BeautifulSoup(html, 'html5lib')
    case_info = {}

    info_table = soup.find('table', summary='Table listing additional information')
    if info_table:
        # Ignore first row (which are table headings)
        info_cells = info_table.find_all('tr')[1].find_all('td')
        case_info['court_type'] = info_cells[0].string
        case_info['proceeding_nature'] = info_cells[1].string
        case_info['office'] = info_cells[2].string
        case_info['language'] = info_cells[3].string
        case_info['action_type'] = info_cells[4].string
        case_info['filing_date'] = info_cells[5].string

        # The FC site has a very strange bug whereby sometimes the file returns
        # a date format of DD-MMM-YY (e.g. 27-MAR-92) instead of YYYY-MM-DD,
        # which is the default. This appears to only happen if the server is
        # queried too often - likely caused by bad localization settings on
        # one of the backup or mirror servers. There is no way to predict when
        # this occurs, as far as I can tell - so we need to detect the date
        # format and convert to ISO if it is not.
        if len(case_info['filing_date']) <= 9:
            # Could have used a regex but probably overkill
            case_info['filing_date'] = datetime.datetime.strptime(
                case_info['filing_date'], "%d-%b-%y").strftime("%Y-%m-%d")

    party_table = soup.find('table', summary='Table listing party information')
    if party_table:
        case_info['parties'] = []
        for i, row in enumerate(party_table.find_all('tr')):
            cells = row.find_all('td', limit=3)
            if cells:
                case_info['parties'].append({})
                case_info['parties'][i-1]['name'] = cells[0].string
                case_info['parties'][i-1]['solicitor'] = cells[1].string
                case_info['parties'][i-1]['lawyer'] = cells[2].string

    related_table = soup.find('table', summary='Table listing related cases information')
    if related_table:
        case_info['related_cases'] = []
        for i, row in enumerate(related_table.find_all('tr')):
            cells = row.find_all('td', limit=3)
            if cells:
                case_info['related_cases'].append({})
                # Another 'bug' in the FC site is lack of data validation for
                # related cases - in some instances, court number is displayed
                # as YY-T-NNN instead of T-NNN-YY, so this needs to be corrected
                cur_re_number = re.sub(r'(\d\d)-(T|A)-(\d+)', r'\2-\3-\1', cells[0].string)
                case_info['related_cases'][i-1]['court_number'] = cur_re_number
                case_info['related_cases'][i-1]['name'] = cells[1].string
                case_info['related_cases'][i-1]['proceeding_type'] = cells[2].string

    ip_table = soup.find('table', summary='Table listing intellectual property information')
    if ip_table:
        case_info['ip'] = []
        for i, row in enumerate(ip_table.find_all('tr')):
            cells = row.find_all('td', limit=2)
            if cells:
                case_info['ip'].append({})
                case_info['ip'][i-1]['ip_name'] = cells[0].string
                case_info['ip'][i-1]['ip_number'] = cells[1].string

    return case_info


def fcparse_re(html):
    """
    Takes HTML text containing electronic docket recorded entries from
    the Federal Court of Canada and returns a Python dictionary containing the
    parsed information, in key-value pairs.
    """
    soup = BeautifulSoup(html, 'html5lib')
    case_info = {}

    info_table = soup.find('table', summary='Table listing court number details')
    if info_table:
        info_rows = info_table.find_all('tr')
        if info_rows:
            case_info['court_number'] = info_rows[0].td.string
            case_info['name'] = info_rows[1].td.string
            case_info['proceeding_category'] = info_rows[2].td.string

    recorded_entries = soup.find('table', summary='Table listing the recorded entry(ies)')
    if recorded_entries:
        case_info['recorded_entries'] = []
        # using a substitute index below because the FC recorded entries table
        # includes blank rows in every other row (odd formatting)
        i = 0
        for row in recorded_entries.find_all('tr'):
            cells = row.find_all('td', limit=4)
            if cells:
                case_info['recorded_entries'].append({})
                case_info['recorded_entries'][i]['doc'] = cells[0].string
                case_info['recorded_entries'][i]['date_filed'] = cells[1].string
                case_info['recorded_entries'][i]['office'] = cells[2].string
                case_info['recorded_entries'][i]['recorded_entry_summary'] = cells[3].string
                i += 1

    return case_info


def merge_dicts(x, y):
    """
    Given two dicts, merge them into a new dict as a shallow copy.
    """
    z = x.copy()
    z.update(y)
    return z


class FCNoResponseException(requests.exceptions.RequestException):
    """
    Federal Court server returned a no response error, please try again.
    """


def request_file(url_stub, court_number):
    """
    Requests a file from the electronic docket and returns the requests object
    containing the HTML response.
    """
    # There are two occasional errors on the FC website if hit with too many
    # queries in a short amount of time:
    #   1) a php error / warning (shows up inline on rendered page)
    #   2) a "no response" error (error page is rendered)
    # The file should be re-downloaded if an error is detected in the
    # respose from FC server
    success = False
    attempts = 1
    MAX_ATTEMPTS = 3
    while attempts <= MAX_ATTEMPTS and not success:
        try:
            r = requests.get(url_stub + court_number)
            if 'no response from the application web server' in r.text.lower():
                raise FCNoResponseException(r.text)
            success = True
            return r
        except FCNoResponseException as e:
            print('Error in FC response:')
            print(e.args[0])
            attempts += 1
            if attempts <= 3:
                print('Retrying... ({0} of {1})'.format(attempts, MAX_ATTEMPTS))
            elif attempts > 3:
                print('FC site returned errors in three attempts. The site may '
                    'be experiencing technical difficulties. Try again later.')


def fcretrieve_re(court_number):
    """
    Retrieves the recorded entries HTML file from the Federal Court of Canada
    electronic docket and returns the html as a unicode string (note that the
    return string will be encoded as latin-1 to reflect encoding on FC docket).
    """
    r = request_file(FC_RE_URL_STUB, court_number)
    return r.text


def fcretrieve_ai(court_number):
    """
    Retrieves the additional information HTML file from  Federal Court of Canada
    electronic docket and returns the html as a unicode string (note that the
    return string will be encoded as latin-1 to reflect encoding on FC docket).
    """
    r = request_file(FC_AI_URL_STUB, court_number)
    return r.text


def main():
    import argparse, json
    from pprint import pprint

    p = argparse.ArgumentParser(description='Retrieve and parse docket '
        'information from the Federal Court of Canada website.')
    p.add_argument('court_numbers', nargs='*',
        help='queries the Federal Court of Canada electronic docket for the '
            'court number(s) provided and parses the case information into '
            'a Python dictionary; outputs a list of dictionaries')
    p.add_argument('-r', '--range', nargs=4,
        metavar=('TYPE', 'BEGIN', 'END', 'YEAR'),
        help='retrieve and parse a range of cases of TYPE (e.g. T or A) from '
            'BEGIN to END in YEAR - for example, "-r T 1 100 14" will retrieve '
            'cases T-1-14 to T-100-14; providing a range will cause other '
            'case numbers provided to be ignored [passing in a large range '
            'will take a significant amount of time]')
    p.add_argument('-i', '--input', metavar='FILENAME',
        type=argparse.FileType('r'),
        help='read input from a specified file; one court number per line'
            '(ignores other specified cases)')
    p.add_argument('-o', '--output', metavar='FILENAME',
        type=argparse.FileType(mode='w', encoding='latin-1'),
        default=sys.stdout,
        help='save output to a specified file')
    p.add_argument('-j', '--json', action='store_true',
        help='output in JSON format')
    p.add_argument('-v', '--verbose', action='store_true',
        help='enable verbose mode')
    args = p.parse_args()

    court_numbers = []
    parsed_list = []
    if args.input:
        if args.verbose:
            print('Reading from input ' + args.input.name)
        for line in args.input.readlines():
            if line.strip() != '':
                court_numbers.append(line.strip())
    elif args.range: # if a range is provided, ignore other case numbers provided
        for case_num in range(int(args.range[1]), int(args.range[2]) + 1):
            case_str = "{}-{}-{}".format(args.range[0], case_num, args.range[3])
            court_numbers.append(case_str)
    elif args.court_numbers:
        court_numbers = args.court_numbers
    elif not args.court_numbers:
        p.print_help()
        exit()

    for court_number in court_numbers:
        if args.verbose:
            print('Retrieving and parsing ' + court_number + '... ', end='')
            sys.stdout.flush()
        re = fcparse_re(fcretrieve_re(court_number))
        ai = fcparse_ai(fcretrieve_ai(court_number))
        merged_info = merge_dicts(re, ai)
        if merged_info: # ignore empty cases (nothing was parsed)
            parsed_list.append(merged_info)
            if args.verbose:
                print('Success.')
                sys.stdout.flush()
        elif args.verbose:
            print('Nothing parsed.')

    if args.json:
        print(json.dumps(parsed_list, indent=4,
            ensure_ascii=False, sort_keys=True), file=args.output)
    else:
        pprint(parsed_list, stream=args.output)


if __name__ == '__main__':
    main()
