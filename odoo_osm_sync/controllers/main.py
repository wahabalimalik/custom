from odoo import http
import requests,json
from bs4 import BeautifulSoup
from gis_geometrics import OSM_Polygon, Overpass
import overpy
from osmapi import OsmApi
from odoo.exceptions import UserError, ValidationError
from odoo.tools.translate import _
import logging

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

		MyApi = OsmApi(username = u"Wahab Ali Malik", password = u"odoo")
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

		MyApi = OsmApi(username = u"Wahab Ali Malik", password = u"odoo")
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
		_logger.info('Receive info for id : %s' %(bus_ids))

		r = requests.get('http://www.openstreetmap.org/api/0.6/way/%s/full' %(bus_ids))
		_logger.info('Get full info of building cornors')

		response = BeautifulSoup(r.text)
		nodes = response.osm.findAll("node")

		lat = []
		lon = []

		for x in nodes:
			lat.append(float(x['lat']))
			lon.append(float(x['lon']))

		min_lat = min(float(s) for s in lat)
		min_lon = min(float(s) for s in lon)
		max_lat = max(float(s) for s in lat)
		max_lon = max(float(s) for s in lon)
		data = """[timeout:10][out:json];
		node(%s,%s,%s,%s);
		(._;>;);
		out;""" %(min_lat,min_lon,max_lat,max_lon,)

		_logger.info('Sending request for nodes near building')


		r = requests.get("http://overpass-api.de/api/interpreter?data=%s" %(data))

		_logger.info('Receive all nodes near building')


		if r.text:
			data = json.loads(r.text)
			data = data['elements']
			row_data = []
			len_tup = 0
			for x in data:
				api = overpy.Overpass()
				buildings = Overpass.getPolygonByWayId(api, int(bus_ids))
				if buildings.isInPolygon(float(str(x['lat'])),float(str(x['lon']))):
					if 'tags' in x:
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
				'building' : building,
				'levels' : levels,
				'material' : material,
				'shop' : shop,
				'types' : types,
				'amenity' : amenity,
				'info_data' : row_data
			}

			res = http.request.env['osm.build'].sudo().create(res)
			return {'row_data' : res.id}