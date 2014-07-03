
if __name__ == '__main__':
    dict = {1 : "2014-06-12",
            2 : "2014-01-01",
            3 : "2015-02-27" }
    lowest_date = min(dict.values())
    for key, value in dict.iteritems():
        if value == lowest_date:
            print key
