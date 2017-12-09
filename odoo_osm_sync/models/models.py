# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import UserError, ValidationError
import requests,json
headers = {'Content-Type': 'application/json'}

# class Osm_Config(models.TransientModel):
#     _inherit = 'base.config.settings'
#     username = fields.Char('User Name')
#     password = fields.Char()

class OsmBuildingData(models.Model):
	_name = 'osm.build'
	_rec_name = 'bus_ids'

	bus_ids = fields.Integer("Building ID")
	street = fields.Char()
	name = fields.Char()
	area = fields.Char()
	building = fields.Char()
	levels = fields.Integer()
	material = fields.Char()
	property_valuation = fields.Float(compute='_compute_valuation',string='Property Valuation')
	property_tax = fields.Float(compute='_compute_tax',string='Property Tax')
	shop = fields.Char()
	types = fields.Char()
	amenity = fields.Char()
	info_data = fields.One2many('info.data', 'info_id')

	@api.one
	@api.depends('property_valuation','building')
	def _compute_tax(self):
		if self.property_valuation and self.building:
			if 'commercial' in self.building:
				self.property_tax = self.property_valuation * 0.20 / 100
			else:
				self.property_tax = self.property_valuation * 0.15 / 100

	@api.one
	@api.depends('area')
	def _compute_valuation(self):
		if self.area:
			self.property_valuation = float(self.area) * 50000

	@api.multi
	def button_open_wizard_tnt(self):
		return {
		'type': 'ir.actions.act_window',
		'name': 'Tenant',
		'res_model': 'build.tnt',
		'view_type': 'form',
		'view_mode': 'form',
		'target' : 'new',
		'context':"{'default_bus_ids': %s}" %(self.bus_ids)
		}

	@api.multi
	def button_open_wizard_own(self):
		return {
		'type': 'ir.actions.act_window',
		'name': 'Owner',
		'res_model': 'res.partner',
		'view_type': 'form',
		'view_mode': 'form',
		'target' : 'new',
		'context':"{'default_bus_ids': %s,'default_area_own': %s}" %(self.id,self.area)
		}

class InfoData(models.Model):
	_name = 'info.data'
	_rec_name = 'tenant'

	types = fields.Char()
	bus_ids = fields.Char()
	lat = fields.Char()
	lon = fields.Char()
	name = fields.Char()
	shop = fields.Char()
	amenity = fields.Char()
	tenant = fields.Char()
	owner = fields.Char()
	citizen = fields.Char()
	rent = fields.Char()
	vrn = fields.Char()
	assess = fields.Char()
	branch = fields.Char()
	tax = fields.Char()
	tin = fields.Char()
	efd = fields.Char()
	valued = fields.Char()

	info_id = fields.Many2one('osm.build',ondelete='cascade')
	tnt_id = fields.Many2one('osm.build',ondelete='cascade')

class osm_build_own(models.Model):
	_name = 'build.own'

	bus_ids = fields.Char(readonly=True)
	name = fields.Char('Owner Name')
	citizen = fields.Boolean()
	vrn = fields.Integer('VRN')
	assess = fields.Boolean()
	branch = fields.Boolean('Branch')
	tax = fields.Float(compute='_compute_tax',string='Total Tenant Tax')
	tin = fields.Char('TIN')
	efd = fields.Char('EFD')
	valued = fields.Char('Valued')
	tenants_id = fields.One2many('build.tnt','tnt_id')

	@api.one
	@api.depends('tenants_id.tax')
	def _compute_tax(self):
		if self.tenants_id:
			self.tax = sum(x.tax for x in self.tenants_id)

	@api.multi
	def create_own(self):
		tenant_name = []
		for x in self.tenants_id:
			tenant_name.append(x.tenant_name.tenant)

		data = {
			"params": 
				{
					"bus_ids" : self.bus_ids,
					"name" : self.name,
					"citizen" : self.citizen,
					"vrn" : self.vrn,
					"assess" : self.assess,
					"branch" : self.branch,
					"tax" : self.tax,
					"tin" : self.tin,
					"efd" : self.efd,
					"valued" : self.valued,
					'tenants_id' : tenant_name
				}
		}

		requests.post('http://139.99.101.43:8000/details/owner/', headers=headers, data=json.dumps(data))
 
class osm_build_tnt(models.Model):
	_name = 'build.tnt'
	tenant_name = fields.Many2one('info.data','Tenant Name',domain=[('tenant', '!=', 'Nr')])
	bus_ids = fields.Char(readonly=True)
	name = fields.Char('Tenant Name')
	citizen = fields.Boolean()
	rent = fields.Integer()
	vrn = fields.Integer('VRN')
	assess = fields.Boolean()
	branch = fields.Boolean()
	tax = fields.Float(compute='_compute_tax')
	tin = fields.Integer('TIN')
	efd = fields.Integer('EFD')
	valued = fields.Integer()

	tnt_id = fields.Many2one('build.own',ondelete='cascade')
	tnt_id_1 = fields.Many2one('res.partner',ondelete='cascade')

	@api.onchange('tenant_name')
	def onchange_tenant_name(self):
		if self.tenant_name:
			print self.tenant_name.citizen
			if self.tenant_name.citizen == 'True':
				self.citizen = True
			self.rent = int(self.tenant_name.rent)
			self.tax = float(self.tenant_name.tax)

	@api.one
	@api.depends('citizen','rent')
	def _compute_tax(self):
		if self.citizen:
			if self.rent:
				self.tax = (self.rent/100) * 10
		else:
			self.tax = (self.rent/100) * 15

	@api.multi
	def create_tnt(self):
		
		data = {"params": {
		"bus_ids" : self.bus_ids,
		"name" : self.name,
		"citizen" : self.citizen,
		"rent" : self.rent,
		"vrn" : self.vrn,
		"assess" : self.assess,
		"branch" : self.branch,
		"tax" : self.tax,
		"tin" : self.tin,
		"efd" : self.efd,
		"valued" : self.valued,
		}
		}
		requests.post('http://139.99.101.43:8000/details/tenant/', headers=headers, data=json.dumps(data))

class ResPartnerExt(models.Model):
	_inherit = 'res.partner'

	bus_ids = fields.Many2one('osm.build',string="Business ID")
	name = fields.Char('Owner Name')
	killbill_id = fields.Char('KillBill ID')
	area_own = fields.Float()
	building = fields.Char(compute='_compute_building')
	property_valuation = fields.Float(compute='_compute_valuation',string='Property Valuation')
	property_tax = fields.Float(compute='_compute_tax',string='Property Tax')
	citizen = fields.Boolean()
	vrn = fields.Integer('VRN')
	assess = fields.Boolean()
	branch = fields.Boolean('Branch')
	tax = fields.Float(compute='_compute_tax',string='Total Tenant Tax')
	tin = fields.Char('TIN')
	efd = fields.Char('EFD')
	valued = fields.Char('Valued')
	tenants_id = fields.One2many('build.tnt','tnt_id_1')
	
	@api.one
	@api.depends('bus_ids.building')
	def _compute_building(self):
		if self.bus_ids.building:
			self.building = self.bus_ids.building

	@api.one
	@api.depends('property_valuation','building')
	def _compute_tax(self):
		if self.property_valuation and self.building:
			if 'commercial' in self.building:
				self.property_tax = self.property_valuation * 0.20 / 100
			else:
				self.property_tax = self.property_valuation * 0.15 / 100

	@api.one
	@api.depends('area_own')
	def _compute_valuation(self):
		if self.area_own:
			self.property_valuation = float(self.area_own) * 50000


	@api.multi
	def create_own(self):
		tenant_name = []
		for x in self.tenants_id:
			tenant_name.append(x.tenant_name.tenant)

		data = {
			"params": 
				{
					"bus_ids" : self.bus_ids,
					"name" : self.name,
					"citizen" : self.citizen,
					"vrn" : self.vrn,
					"assess" : self.assess,
					"branch" : self.branch,
					"tax" : self.tax,
					"tin" : self.tin,
					"efd" : self.efd,
					"valued" : self.valued,
					'tenants_id' : tenant_name
				}
		}

		requests.post('http://localhost:8069/details/owner/', headers=headers, data=json.dumps(data))
