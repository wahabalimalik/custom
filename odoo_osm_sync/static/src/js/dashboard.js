odoo.define('osm_dashboard', function (require) {
"use strict";

var core = require('web.core');
var Widget = require('web.Widget');
var Model = require('web.Model');
var session = require('web.session');
var PlannerCommon = require('web.planner.common');
var framework = require('web.framework');
var webclient = require('web.web_client');
var PlannerDialog = PlannerCommon.PlannerDialog;

var QWeb = core.qweb;
var _t = core._t;

var cache = {};
var data = {};
var res = undefined;
var data_table = undefined;

var Dashboard = Widget.extend({
    template: 'DashboardOsm',

    events: {
        'click .search-button': 'search_init',
        'click .pop': 'popup',
    },

    init: function(parent, data){

        return this._super.apply(this, arguments);
    },
    start: function(){

        return this._super.apply(this, arguments);
    },
    search_init: function(){
    	var self = this;
    	var area = $('#search_area').val();
    	if (area.length === 0) { alert('Please fill your Area field'); return true;}

    	var animate = $(".osm-search-chart").animate(
    		{'margin-top': '0vh'}, 
    		1000,
    		function(){
    			proceed();
    		}
		);
		
		function proceed() {

			try {
			    area_code(area);
			}
			catch(err) {
			    alert('OSM not recoignise ' + area + ' as an area')
			    return true;
			}

			fetch_data();

	        self.load().done(data_table.replace(self.$('.osm-search-result')));
		}
		function area_code(area,callback) {
	    	var area_code_value = $.ajax(
			    "https://nominatim.openstreetmap.org/search" +
			    "?X-Requested-With=overpass-turbo",
			    {
			    	async: false,
			        data: 
			        {
						format: "json",
						q: area
			        },
			        success: function(data) {
						if (typeof data == "string") {
							try {
								data = JSON.parse(data);
							} catch (e) {}
						}
						cache[area] = data[0];
			        },
			        error: function() {
						var err =
							"An error occurred while contacting the osm search server nominatim.openstreetmap.org :(";
						console.log(err);

			        }
			    }
			);
			res = cache[area];
			var area_ref = 1 * res.osm_id;

			if (res.osm_type == "way") area_ref += 2400000000;
			if (res.osm_type == "relation") area_ref += 3600000000;
			res = "area(" + area_ref + ")";
		}
		function fetch_data(){
			var query = '[out:json][timeout:25];\
				'+res+'->.searchArea;\
				(\
					way["building"](area.searchArea);\
					);\
					out body;\
				>;\
				out skel qt;';
			query.trim();
			var query_lang = 'OverpassQL';
			var cache = undefined;
			var shouldCacheOnly = undefined;
			var server = '//overpass-api.de/api/';
			var user_mapcss = undefined;
			run_query(query,query_lang,cache,shouldCacheOnly,server,user_mapcss);
		}
		function run_query(query,query_lang,cache,shouldCacheOnly,server,user_mapcss) {
	    	var request_headers = {"X-Requested-With": "overpass-turbo"};
		    var ajax_request = {};
		    
		    var onSuccessCb = function(data, textStatus, jqXHR) {
		    	if (jqXHR.responseText) {
		    		var myArr = JSON.parse(jqXHR.responseText);
		    	}
		    }
		    ajax_request = $.ajax(
		        server + "interpreter",
		        {
					type: "POST",
					async: false,
					data: {data: query},
					headers: request_headers,
					success: onSuccessCb,
					error: function(jqXHR, textStatus, errorThrown) {
					console.log(errorThrown);
		        }
		    }).done(function(results) {
		        	data = results;
			});
	    }
	},
    load: function(){

        var loading_done = new $.Deferred();
        this.load_records(data);

        loading_done.resolve();
        return loading_done;
    },
    load_records: function(data){
    	data_table = new SearchResult(this, data);
        return  data_table;
    },
    popup: function(e){
    	self = this
    	var id =  $(e.currentTarget).attr('id')
    	var result = $.grep(data.elements, function(e){ return e.id == id; });
    	var bus_ids = result[0]['id'];
		var street = result[0]['tags']['addr:street'];
		var name = result[0]['tags']['name'];
		var building = result[0]['tags']['building'];
		var levels = result[0]['tags']['building:levels'];
		var material = result[0]['tags']['building:material'];
		var shop = result[0]['tags']['shop'];
		var types = result[0]['tags']['type'];
		var amenity = result[0]['tags']['amenity'];

		console.log(bus_ids,street,name,building,levels,material,shop,types,amenity);

		session.rpc("/details/business", 
		{
			bus_ids : bus_ids || 'N/A',
			street : street || 'N/A',
			name : name || 'N/A',
			building : building || 'N/A',
			levels : levels || 'N/A',
			material : material || 'N/A',
			shop : shop || 'N/A',
			types : types || 'N/A',
			amenity : amenity || 'N/A',

		}).then(function (res) {
			console.log(res);
    		self.do_action('odoo_osm_sync.action_window_buss',{});
        });
    },
});


var SearchResult = Widget.extend({
    template: 'SearchResult',

    init: function(parent, data){

    	this.data = data;
    	this.parent = parent;
    	return this._super.apply(this, arguments);
    },
    start: function(){
    	this.push_data();
        return this._super.apply(this, arguments);
    },
    push_data: function() {

    	$('div.osm-result-chart > table >tbody > tr').remove();
	    for (var i = 0; i < data.elements.length; i++) {
	    // for (var i = 0; i < 100; i++) {
	    	if (data.elements[i].hasOwnProperty('tags')){
				if (this.has_data(i,'addr:street')) {var street=this.is_data(i,'addr:street')}else{var street='N/A';}
				if (this.has_data(i,'name')) {var name=this.is_data(i,'name')}else{var name = 'N/A';}
				if (this.has_data(i,'building')) {var building=this.is_data(i,'building')}else{var building = 'N/A';}
				$('div.osm-result-chart > table >tbody').append(
					"<tr>\
						<td><button id = "+data.elements[i].id+" class='pop' value = "+data.elements[i].id+">"+data.elements[i].id+"</button></td>\
						<td>"+street+"</td>\
						<td>"+name+"</td>\
						<td>"+building+"</td>\
					</tr>"
				);
	    	}
	    }
    },
    has_data: function(number,check) {

    	if (data.elements[number].tags.hasOwnProperty(check)){return true;}else{return false;}
    },
    is_data: function(number,check) {
    	var name = data.elements[number].tags[check];
    	return name
    },
});

core.action_registry.add('odoo_osm_sync.dashboard', Dashboard);

return {
    Dashboard: Dashboard,
};

});
