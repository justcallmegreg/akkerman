# This package will contain the akkerman spiders.
#
# Each spider module defines a scrapy.Spider subclass that crawls a target
# site and yields Items (see akkerman/items.py). The ParquetPipeline lands the
# yielded items into data/<spider>_<timestamp>.parquet.
