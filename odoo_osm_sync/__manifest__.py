# -*- coding: utf-8 -*-
{
    'name': "odoo Osm Sync",

    'summary': """
        Sync with OSM for targited opration""",

    'description': """
Sync with OSM (Open Street Map)
===============================
Retriving:
----------
        i) All buildings data.
        ii)All business in building.
Adding:
-------
        i)Owners in Building.
        ii)Tenant in Builing.
    """,

    'author': "Wahab Ali Malik",
    'website': "http://www.glarecom.com",

    'category': 'Sync',
    'version': '0.1',

    'depends': ['base'],
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
    ],
    'qweb': [
        'static/src/xml/dashboard.xml',
        ],

}