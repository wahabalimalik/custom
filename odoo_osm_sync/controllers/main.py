from odoo import http
import requests,json
from bs4 import BeautifulSoup
from gis_geometrics import OSM_Polygon, Overpass
import overpy
from osmapi import OsmApi
from odoo.exceptions import UserError, ValidationError
from odoo.tools.translate import _
import logging
import numpy as np
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
import pyproj
from shapely.geometry import shape
from shapely.ops import transform
from functools import partial

_logger = logging.getLogger(__name__)


class Osm(http.Controller):
	@http.route('/details/owner', type='json', auth="none")
	def osm_owner(self, **kw):

		bus_ids = http.request.params['bus_ids']
		name = http.request.params['name']
		citizen = http.request.params['citizen']
		vrn = http.request.params['vrn']
		assess = http.request.params['assess']
		branch = http.request.params['branch']
		tax = http.request.params['tax']
		tin = http.request.params['tin']
		efd = http.request.params['efd']
		valued = http.request.params['valued']
		tenants_id = http.request.params['tenants_id']


		r = requests.get('http://www.openstreetmap.org/api/0.6/way/%s/full' %(bus_ids))
		response = BeautifulSoup(r.text)
		nodes = response.osm.findAll("node")

		lat = 0
		lon = 0
		for x in nodes:
			lat = lat + float(x['lat'])
			lon = lon + float(x['lon'])
		lat = lat / len(nodes)
		lon = lon / len(nodes)

		MyApi = OsmApi(username = u"Wahab Ali Malik", password = u"Loveodoo")
		MyApi.ChangesetCreate({u"comment": u"Adding One of the owner of building"})
		print MyApi.NodeCreate({u"lon":lon, u"lat":lat, u"tag": {
			u"owner":u"%s" %(name),
			u"citizen":u"%s" %(citizen),
			u"vrn":u"%s" %(vrn),
			u"assess":u"%s" %(assess),
			u"branch":u"%s" %(branch),
			u"tax":u"%s" %(tax),
			u"tin":u"%s" %(tin),
			u"efd":u"%s" %(efd),
			u"valued":u"%s" %(valued),
			u"tenants_id":u"%s" %(tenants_id),
			}})

	@http.route('/details/tenant', type='json', auth="none")
	def osm_tenant(self, **kw):

		bus_ids = http.request.params['bus_ids']
		name = http.request.params['name']
		citizen = http.request.params['citizen']
		rent = http.request.params['rent']
		vrn = http.request.params['vrn']
		assess = http.request.params['assess']
		branch = http.request.params['branch']
		tax = http.request.params['tax']
		tin = http.request.params['tin']
		efd = http.request.params['efd']
		valued = http.request.params['valued']

		r = requests.get('http://www.openstreetmap.org/api/0.6/way/%s/full' %(bus_ids))
		response = BeautifulSoup(r.text)
		nodes = response.osm.findAll("node")

		lat = 0
		lon = 0
		for x in nodes:
			lat = lat + float(x['lat'])
			lon = lon + float(x['lon'])
		lat = lat / len(nodes)
		lon = lon / len(nodes)

		MyApi = OsmApi(username = u"Wahab Ali Malik", password = u"Loveodoo")
		MyApi.ChangesetCreate({u"comment": u"Adding One of the owner of building"})
		print MyApi.NodeCreate({u"lon":lon, u"lat":lat, u"tag": {

			u"tenant":u"%s" %(name),
			u"vrn":u"%s" %(vrn),
			u"assess":u"%s" %(assess),
			u"branch":u"%s" %(branch),
			u"tin":u"%s" %(tin),
			u"efd":u"%s" %(efd),
			u"citizen":u"%s" %(citizen),
			u"valued":u"%s" %(valued),
			u"rent":u"%s" %(rent),
			u"tax":u"%s" %(tax),
			}})

	@http.route('/details/business', type='json', auth="none")
	def osm_overpass(self, **kw):
		_logger.info('Receive info for id : %s' %(http.request.params["bus_ids"]))

		# Assign Variables
		bus_ids = http.request.params["bus_ids"]
		street = http.request.params["street"]
		name = http.request.params["name"]
		building = http.request.params["building"]
		levels = http.request.params["levels"]
		material = http.request.params["material"]
		shop = http.request.params["shop"]
		types = http.request.params["types"]
		amenity = http.request.params["amenity"]
		bus_ids = int(str(bus_ids).replace(',',''))

		# Creating polygon
		query = "[timeout:10][out:json];way(%s);(._;>;);out body;" %(bus_ids)
		r = requests.get("http://overpass-api.de/api/interpreter?data=%s" %(query))
		data = json.loads(r.text)
		cordinates = []
		for y in [x['nodes'] for x in data['elements'] if x["type"] == 'way'][0]:
			cordinates.append([(x['lat'], x['lon'] )for x in data['elements'] if x["id"] == y][0])
		building_polygon = np.array(cordinates)

		# Calculate area of polygon
		geom = {'type': 'Polygon',
		'coordinates': [building_polygon]}
		s = shape(geom)
		proj = partial(pyproj.transform, pyproj.Proj(init='epsg:4326'),pyproj.Proj(init='epsg:3857'))
		s_new = transform(proj, s)
		projected_area = transform(proj, s).area
		
		# Retrive nodes near Cordinates
		min_lat = building_polygon.min(axis=0)[0]
		min_lon = building_polygon.min(axis=0)[1]
		max_lat = building_polygon.max(axis=0)[0]
		max_lon = building_polygon.max(axis=0)[1]
		data = """[timeout:10][out:json];
		node(%s,%s,%s,%s);
		(._;>;);
		out;""" %(min_lat,min_lon,max_lat,max_lon,)
		_logger.info('Sending request for nodes near building')
		r = requests.get("http://overpass-api.de/api/interpreter?data=%s" %(data))
		_logger.info('Receive all nodes near building')
		
		# Filter data and assign requried data to keys in dictionary
		data = json.loads(r.text)
		data = data['elements']
		polygon = Polygon(cordinates)
		row_data = []
		len_tup = 0
		for x in data:
			if 'tags' in x and polygon.contains(Point(float(str(x['lat'])),float(str(x['lon'])))):
				_logger.info('looping through data')
				row_data.append((0,len_tup,{
					'types' : str(x['type'] if 'type' in x else "NR"),
					'bus_ids' : str(x['id'] if 'id' in x else "Nr"),
					'lat' : str(x['lat'] if 'lat' in x else "Nr"),
					'lon' : str(x['lon'] if 'lon' in x else "Nr"),
					'name' : str(x['tags']['name'] if 'name' in x['tags'] else "Nr"),
					'shop' : str(x['tags']['shop'] if 'shop' in x['tags'] else "Nr"),
					'amenity' : str(x['tags']['amenity'] if 'amenity' in x['tags'] else "Nr"),
					'tenant' : str(x['tags']['tenant'] if 'tenant' in x['tags'] else "Nr"),
					'owner' : str(x['tags']['owner'] if 'owner' in x['tags'] else "Nr"),
					'citizen' : str(x['tags']['citizen'] if 'citizen' in x['tags'] else "Nr"),
					'rent' : str(x['tags']['rent'] if 'rent' in x['tags'] else "Nr"),
					'vrn' : str(x['tags']['vrn'] if 'vrn' in x['tags'] else "Nr"),
					'assess' : str(x['tags']['assess'] if 'assess' in x['tags'] else "Nr"),
					'branch' : str(x['tags']['branch'] if 'branch' in x['tags'] else "Nr"),
					'tax' : str(x['tags']['tax'] if 'tax' in x['tags'] else "Nr"),
					'tin' : str(x['tags']['tin'] if 'tin' in x['tags'] else "Nr"),
					'efd' : str(x['tags']['efd'] if 'efd' in x['tags'] else "Nr"),
					'valued' : str(x['tags']['valued'] if 'valued' in x['tags'] else "Nr"),
				}))
				len_tup = len_tup +1
		res = {
			'bus_ids' : bus_ids,
			'street' : street,
			'name' : name,
			'area' : projected_area,
			'building' : building,
			'levels' : levels,
			'material' : material,
			'shop' : shop,
			'types' : types,
			'amenity' : amenity,
			'info_data' : row_data
		}
		http.request.env['osm.build'].sudo().search([]).unlink()
		res = http.request.env['osm.build'].sudo().create(res)
		return res.id
