# CHGIS Temporal Gazetteer (TGAZ) API — TGW site snapshot

Source: https://chgis.hudci.org/tgw/

Fetched on: 2025-11-02

Note: The content below was automatically fetched and is a partial extract of the page's main content. For the authoritative and complete version, visit the source link above.

---

## Introduction

TGAZ API - is a read-only interface designed to search the contents of the [China Historical GIS](http://www.fas.harvard.edu/~chgis/) placename database. The TGAZ system architecture -- based loosely on the CHGIS XML API (2006) -- has been normalized and made more generic in order to integrate multiple data sources, and to allow for vernacular spellings or transcription methods in many languages.

This interface accepts queries for placenames in UTF-8 encoded strings or glyphs (for example, Chinese Simplified or Complex characters). Each placename recorded in the database is referred to as a spelling. A brief look at the project in diagrams (PDF): https://chgis.hudci.org/tgw/docs/TemporalGazetteer_Slides_20140501.pdf

...

## Usage

The TGAZ web service is designed to receive RESTful URIs containing query values, and to return the results in XML format by default. The interface is READ-ONLY and currently provides two functions:

1. Canonical Placename Search — http://maps.cga.harvard.edu/tgaz/placename/UNIQUE_ID
2. Faceted Search — http://maps.cga.harvard.edu/tgaz/placename?QUERY_PARAMETER=VALUE

Instructions:

1. Canonical Placename Records — replace UNIQUE_ID with the unique placename ID to be searched. (The IDs being used are minted for the TGAZ database with the prefix hvd_. For example, the IDs listed in the CHGIS data layers would have the prefix added, such as CHGIS ID 32180 = TGAZ ID hvd_32180).

...

2. Faceted Search — allows for a combination of query parameters to be searched. A PLACENAME, YEAR, FEATURE TYPE, DATA SOURCE, and IMMEDIATE PARENT can be sent in the form of a query string, such as: `?n=mengla&yr=1820&ftyp=xian`. Note: the default output is XML, which can be reset using a FORMAT parameter, such as `fmt=json`.

Blank spaces are accepted in the PLACENAME, FEATURE TYPE, IMMEDIATE PARENT values. Chinese Characters should be sent as plain UTF-8 encodings, not URL-encoded hexadecimal strings. Note: for historical records the valid years of the database are -222 to 1911.

...

## Canonical Placename

- https://chgis.hudci.org/tgaz/placename/hvd_32180

Canonical Placename Formats

- json https://chgis.hudci.org/tgaz/placename/json/hvd_80547
- rdf https://chgis.hudci.org/tgaz/placename/rdf/hvd_135744
- html https://chgis.hudci.org/tgaz/placename/html/hvd_9732
- xml https://chgis.hudci.org/tgaz/placename/xml/hvd_96066

...

## Faceted Search

Parameters allowed:

- n: name (the spelling of the placename)
- yr: year of existence (the year during which the placename existed)
- ftyp: feature type (the class of placename)
- src: source (the data source, such as CHGIS, RAS)
- p: part of (the immediate parent jurisdiction where the place was located)
- fmt: format (the output format returned: xml, json, html)

Placename Examples

- https://chgis.hudci.org/tgaz/placename?n=tianbian
- https://chgis.hudci.org/tgaz/placename?n=%E6%99%8B%E9%98%B3 (晋阳)

Placename & Format Examples

- https://chgis.hudci.org/tgaz/placename?fmt=json&n=%E6%BB%9A%E5%BC%84 (滚弄)
- https://chgis.hudci.org/tgaz/placename?fmt=html&n=Rui%27an%20Xian
- https://chgis.hudci.org/tgaz/placename?fmt=xml&n=%E6%B8%A9%E5%B7%9E (温州)

Placename & Year Examples

- https://chgis.hudci.org/tgaz/placename?fmt=html&n=%E9%BE%8D&yr=800 (龍)
- https://chgis.hudci.org/tgaz/placename?fmt=html&n=%E9%9B%99&yr=300 (雙)

Placename & Feature Type Examples

- https://chgis.hudci.org/tgaz/placename?fmt=html&n=meng&ftyp=%E5%B7%9E (州)
- https://chgis.hudci.org/tgaz/placename?fmt=html&n=%E9%AE%91&ftyp=cun%20zhen (鮑 / cun zhen)

Placename & Part-of Parent Unit Examples

- https://chgis.hudci.org/tgaz/placename?fmt=html&n=%E8%8C%B9&p=%E4%B8%8A%E8%B0%B7%E9%83%A1 (茹 in 上谷郡)
- https://chgis.hudci.org/tgaz/placename?fmt=html&n=%E7%9B%A7%E6%BA%AA&p=%E9%BB%94%E4%B8%AD (盧溪 in 黔中)

Multi-Parameter Faceted Search Examples

- https://chgis.hudci.org/tgaz/placename?fmt=html&n=%E5%BA%86&ftyp=xian&yr=1420&p=Chuzhou (庆, county, year 1420, parent Chuzhou)

...

© 2014 Lex Berman and Bill Hays  
Temporal Gazetteer Home Page: https://chgis.hudci.org/tgw/index.html

