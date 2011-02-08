#!/usr/bin/python
# -*- coding: UTF-8 -*-

import optparse
import urllib
import csv
import simplejson
import pprint

class OABatchGeoCoder(object):
    """
    OpenAddresses.ch Batch Geocoder
    City, Street, Housenumer to Lat/Lon
    Format input csv: city;street;housenumber
    
    @author: Christian Karrié <christian@karrie.info>    
    """
    def __init__(self, args):
        self.input_file = args[0]
        self.output_file = args[1]
        self.addresses = []
        self.reader = None
        self.writer = None
        self.input_cols = ['postcode','city', 'street', 'housenumber']
        self.output_cols = self.input_cols + ['lon', 'lat']
        self.base_url = 'http://www.openaddresses.org/addresses/'
        
    def read(self, format='CSV'):
        print "Reading input file %s ..." %self.input_file
        try:
            if format == 'CSV':
                _file = open(self.input_file, 'rb')
                reader = csv.reader(_file, delimiter=';')            
            
            for i, row in enumerate(reader):
                if i == 0:
                    if row != self.input_cols:
                        raise ValueError('Row Header (first line) must look like %s!' %';'.join(self.input_cols))
                else:
                    if len(row) != len(self.input_cols):
                        raise ValueError('Row length must be 3 cols!')
                    self.addresses.append(row)
                    
        except csv.Error, e:
            raise Exception("Fehler beim Lesen der CSV %s: Zeile %d: %s" %(self.input_file, reader.line_num, e))
        finally:
            _file.close()
        print "... got %d addresses" %(len(self.addresses))
    
    def _geocode(self, query, additional={}):        
        query.update(additional)
        p = urllib.urlencode(query)
        url = self.base_url + '?' + p
        f = urllib.urlopen(url)
        try:
            content = f.headers['Content-Type']
            if f.code == 200:
                if 'json' in content:
                    decoded = simplejson.load(f)
                    try:
                        coords = decoded['features'][0]['geometry']['coordinates']
                    except IndexError:
                        coords = [None, None]
                    
                    return coords
                else:
                    raise Exception("Decoder for Content-Type %s not implemented" %content)
            else:
                raise Exception("Server returned Code %d!" %f.code)
        # Unschoener Code:        
        except AttributeError:
            decoded = simplejson.load(f)
            try:
                coords = decoded['features'][0]['geometry']['coordinates']
            except IndexError:
                coords = [None, None]
            return coords
    
    def geocode_all(self):
        base_params = {'queryable':','.join(self.input_cols)}
        for i, addr in enumerate(self.addresses):
            addr_prm = {               
                'postcode__eq': addr[0], 
                'city__ilike': addr[1],
                'street__ilike': addr[2],
                'housenumber__eq': addr[3]
            }
            
            additional = {
                'limit':1
            }
            
            addr_prm.update(base_params)            
            res = self._geocode(addr_prm, additional)
            addr += res
            if res[0] and res[1]:
                print '> #%d: found %s %s %s @ %.3f %.3f' %(i, addr[1], addr[2], addr[3], res[0], res[1])         
            else:
                print '> #%d: coordinates of address %s %s %s not found :-(' %(i, addr[1], addr[2], addr[3])
    
    def write(self, format='CSV'):
        print "Writing addresses to %s, it will overwrite existing files!" %(self.output_file)        
        try:
            if format == 'CSV':
                _file = open(self.output_file, "wb")
                writer = csv.writer(_file, delimiter = ';')
                writer.writerow(self.output_cols)
                writer.writerows(self.addresses)
        finally:
            _file.close()
            
    def statistics(self):
        failed = 0.0
        count = len(self.addresses)
        for addr in self.addresses:
            if not all(addr[-2:]):
                failed += 1.0             
        print "%d of %d addresses successfully geocoded (%.2f%%)" %(count-failed, count, ((count-failed)/count)*100.0)

if __name__=="__main__":   
    #parser = optparse.OptionParser("%prog <input>.csv <output>.csv")
    #(options, args) = parser.parse_args()
    args = ['input.csv', 'out.csv']
    if len(args) != 2:
        #parser.error("incorrect number of arguments")
        pass
        
    else:        
        oa = OABatchGeoCoder(args)
        oa.read()        
        oa.geocode_all()
        oa.write()
        oa.statistics()

