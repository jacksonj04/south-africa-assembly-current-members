# coding=utf-8

import scraperwiki
import lxml.html
import sqlite3
import re
import urllib2
import time

BASE_URL = 'https://www.parliament.gov.za/group-details/2'

opener = urllib2.build_opener()
opener.addheaders = [('User-Agent', 'mySociety Scraper')]
response = opener.open(BASE_URL)
html = response.read()

ssRoot = lxml.html.fromstring(html)

PARTY_MAP = {
    'ACDP':     'Q268613',
    'AGANG SA': 'Q4969082',
    'AIC':      'Q4689795',
    'ANC':      'Q83162',
    'APC':      'Q384266',
    'COPE':     'Q1125988',
    'DA':       'Q761877',
    'EFF':      'Q15613585',
    'FF PLUS':  'Q510163',
    'IFP':      'Q654444',
    'NFP':      'Q6972795',
    'PAC':      'Q775460',
    'UDM':      'Q1788070',
}

DISTRICT_MAP = {
    'Eastern Cape':  'Q130840',
    'Free State':    'Q160284',
    'Gauteng':       'Q133083',
    'KwaZulu-Natal': 'Q81725',
    'Limpopo':       'Q134907',
    'Mpumalanga':    'Q132410',
    'North West':    'Q165956',
    'Northern Cape': 'Q132418',
    'Western Cape':  'Q127167',
}

linksList = ssRoot.cssselect('div.page-content li a')

parsedMembers = []

for link in linksList:

    href = link.attrib['href']

    pattern = re.compile("^\/person-details\/([0-9]+)$")
    if pattern.match(href):

        memberData = {}

        idRegex = pattern.search(href)
        memberData['id'] = idRegex.group(1)
        memberData['url'] = 'https://www.parliament.gov.za/person-details/' + memberData['id']

        opener = urllib2.build_opener()
        opener.addheaders = [('User-Agent', 'mySociety Scraper')]
        response = opener.open(memberData['url'])
        html = response.read()

        memberRoot = lxml.html.fromstring(html)

        nameString = memberRoot.cssselect('div.page-header h4')[0].text.strip()
        nameRegex = re.search('(.+?) (.+)', nameString)

        memberData['name'] = nameRegex.group(2)
        memberData['honorific'] = nameRegex.group(1)

        content = memberRoot.cssselect('div.page-content')[0]

        strongElements = content.cssselect('strong')

        # # If the first strongElement text is not None, it's something interesting
        # if strongElements[0].text != None:
        #     memberData['role'] = strongElements[0].text
        #     # Remove it so everything else lines up
        #     del strongElements[0]

        # # National or provincial?
        # if strongElements[3] == 'national list':
        #     memberData['type'] = 'national'
        # else if strongElements[3] == 'provincial list':
        #     memberData['type'] = 'provincial'


        partyRegex = re.search('Member of the <strong><a href="\/party-details\/(.+?)">(.+?)<\/a><\/strong>', html)
        memberData['party_code'] = partyRegex.group(1)
        memberData['party_name'] = partyRegex.group(2)

        nationalRegex = re.compile('On the <strong>national list</strong>\.')
        provinceRegex = re.compile('On the <strong>provincial list</strong> for the province of <strong>(.+?)<\/strong>\.')

        if nationalRegex.search(html):
            memberData['type'] = 'national'

        elif provinceRegex.search(html):
            memberData['type'] = 'provincial'
            memberData['district'] = provinceRegex.search(html).group(1)

            if memberData['district'] in DISTRICT_MAP:
                memberData['district_id'] = DISTRICT_MAP[memberData['district']]
            else:
                print '(!) Missing district ID for {}'.format(memberData['district'])

        else:
            memberData['type'] = 'unknown'
            print '(!) Unknown member type!'

        partyRegex = re.search('Member of the <strong><a href="\/party-details\/(.+?)">(.+?)<\/a><\/strong>', html)
        memberData['party_code'] = partyRegex.group(1)
        memberData['party_name'] = partyRegex.group(2)

        if memberData['party_code'] in PARTY_MAP:
            memberData['party_id'] = PARTY_MAP[memberData['party_code']]
        else:
            print '(!) Missing party ID for {}'.format(memberData['party_code'])

        print memberData['name']

        parsedMembers.append(memberData)

        time.sleep(0.5)

print 'Counted {} Members'.format(len(parsedMembers))

try:
    scraperwiki.sqlite.execute('DELETE FROM data')
except sqlite3.OperationalError:
    pass
scraperwiki.sqlite.save(
    unique_keys=['id'],
    data=parsedMembers)
