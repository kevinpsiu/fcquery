# fcquery.py
A Python script to easily query and parse the Federal Court of Canada electronic docket, providing a simple, structured output (including JSON output).

### Installation & Compatibility
Download fcquery.py onto your computer, and run on the command line with the following once you have navigated to the folder containing fcquery.py:

    python fcquery.py

Fcquery.py works on any system that Python supports - Windows XP/Vista/7/8/10, OSX, and Linux/Unix systems. Requires Python 3+. Install Python from http://www.python.org.

### Usage
#### Retrieve a case
The simplest way to use fcquery.py is to query a single case from the Federal Court database, which will result in a structured output in the form of a Python `dict`. For example:

    python fcquery.py T-2103-07

(This may take a few seconds, as the script needs to connect to the Court database and parse the information). The output will be structured data retrieved from the Federal Court, like the following:

```
[{'action_type': 'Non-Action',
  'court_number': 'T-2103-07',
  'court_type': 'Federal Court',
  'filing_date': '2007-12-04',
  'ip': [{'ip_name': "COTE D'OR WORK", 'ip_number': '-'},
         {'ip_name': "KCI COTE D'OR", 'ip_number': '1053502'},
         {'ip_name': 'KFB', 'ip_number': '1006935'},
         {'ip_name': "COTE D'OR", 'ip_number': '-'},
         {'ip_name': 'KCI', 'ip_number': '-'}],
  'language': 'English',
  'name': 'KRAFT CANADA INC v. EURO EXCELLENCE INC.',
  'office': 'Toronto',
  'parties': [{'lawyer': 'LOWMAN, TIMOTHY M',
               'name': 'KRAFT CANADA INC',
               'solicitor': 'Sim Lowman Ashton & McKay LPP'},
              {'lawyer': 'GOUDREAU, PATRICK',
               'name': 'EURO EXCELLENCE INC',
               'solicitor': 'McMillan LLP'}],
  'proceeding_category': 'Applications',
  'proceeding_nature': 'Copyright Infringement [Applications]',
  'recorded_entries': [{'date_filed': '2009-01-22',
                        'doc': '58',
                        'office': 'Montréal',
                        'recorded_entry_summary': 'Reasons for assessment '
                                                  'of costs rendered by '
                                                  'Diane Perrier, '
                                                  'Assessment Officer on '
                                                  '22-JAN-2009 filed on '
                                                  '22-JAN-2009'},
  ...
 'related_cases': [{'court_number': 'A-258-04',
                     'name': 'EURO EXCELLENCE INC. c. KRAFT CANADA INC. '
                             'ET AL',
                     'proceeding_type': 'Appeal (S.27 - Final) - '
                                        'Copyright Act'}]}]
```

#### Multiple cases
You can also query multiple cases simply by adding more court file numbers:

    python fcretriever.py T-2103-07 T-200-15 A-48-14

And so on. 

The default output is in the form of a Python `list` containing `dict`s representing each case.

#### Range of cases
If you want to retrieve a *range* of cases, for example, all cases from T-1-12 to T-100-12, you can use the `-r` flag, like the following:

    python fcretriever.py -r T 1 100 12

This will tell the script that you want file numbers 1 to 100 in year 2012. 

**Warning:** retrieiving a large number of cases will result in performance degradation, and may take a significant amount of time. Depending on the amount of data available for each case and the speed of your internet connection, it may take anywhere from 3-20 seconds per case.

#### Output to JSON
If you do not intend to use the script with other Python scripts, a better output option will be [JSON](http://json.org/) (JavaScript Object Notation), which is a standard and portable data format used in many applications. Simply add a `-j` or `--json` flag, like so:

    python fcretriever.py T-2003-10 -j

This will provide the following sample output:

```
[
    {
        "action_type": "Ordinary",
        "court_number": "T-2003-10",
        "court_type": "Federal Court",
        "filing_date": "2010-12-01",
        "language": "English",
        "name": "JMP ENGINEERING INC. v. JMP ENGINEERING LTD. ET AL",
        "office": "Toronto",
        "parties": [
            {
                "lawyer": "ANISSIMOFF, SERGE",
                "name": "JMP ENGINEERING INC",
                "solicitor": "Anissimoff Mann"
            },
            {
                "lawyer": "-",
                "name": "JMP ENGINEERING LTD",
                "solicitor": "-"
            },
            {
                "lawyer": "-",
                "name": "JMP ROBOTICS INC",
                "solicitor": "-"
            }
        ],
        "proceeding_category": "Actions",
        "proceeding_nature": "Trade Mark Infringement",
        "recorded_entries": [
            {
                "date_filed": "2011-06-09",
                "doc": "-",
                "office": "Ottawa",
                "recorded_entry_summary": "Covering letter from Plaintiff dated 09-JUN-2011 concerning Doc. No. 3 placed on file on 09-JUN-2011"
            },
            ...
        ]
    }
]
```

#### Output to file
You can redirect the output to a file rather than displaying on screen:

   python fcretriever.py A-305-09 -o output.txt

#### Input from file
You can also provide a text file containing a number of cases (one per line), like so:

input.txt:
```
T-539-09
T-1005-10
A-340-13
A-455-14
```

And then run:

    python fcretriever.py -i input.txt 

Of course, you can still direct the output to a file:

    python fcretriever.py -i input.txt -o output.txt

#### Verbose mode
If the script is taking a long time, or you want to keep track of the status on your console, use `-v` for verbose mode:

    python fcretriever.py T-102-09 A-99-14 -v

And it will show a status, like:
  
    Retrieving and parsing T-102-09...


