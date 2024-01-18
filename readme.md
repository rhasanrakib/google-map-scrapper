# Review scrapper from google maps

### installation
```sh
pip install -r requirements.txt
playwright install
```

### usages
Create a location.csv with 3 columns sn,lat,lon,search_key. If there is no keyword then keep it blank. Reviews will store in json file by semi-colon separated sentences

### run
```python scrap.py```