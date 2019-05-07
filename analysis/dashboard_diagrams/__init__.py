import numpy as np
from bokeh.io import output_notebook, output_file, show
from bokeh.plotting import figure, show, gmap, Figure
from bokeh.layouts import column, layout
from bokeh.models.glyphs import Quad, Line
from bokeh.models import ColumnDataSource, GMapOptions, Legend, DataTable, TableColumn,BasicTickFormatter,\
    HoverTool
from bokeh.models import CustomJS, CustomJSFilter, CDSView
from bokeh.models.widgets import RangeSlider, Panel, Tabs, Slider
import pandas as pd
from math import pi
from bokeh.transform import cumsum
from database.dbConnection import *
from bokeh.io import curdoc
from bokeh.palettes import Category20c
from bokeh.tile_providers import CARTODBPOSITRON
import math
from bokeh.embed import components
from ast import literal_eval
from datetime import datetime


def merc(lat, lon):
    r_major = 6378137.000
    x = r_major * math.radians(lon)
    scale = x / lon
    y = 180.0 / math.pi * math.log(math.tan(math.pi / 4.0 +
                                            lat * (math.pi / 180.0) / 2.0)) * scale
    return x, y


housing_n = get_data()
valueOfSqM = 10.76
housing_n = housing_n.drop(["sqft_living15", "sqft_lot15", 'waterfront'], axis=1)
housing_n['floors'] = housing_n['floors'].str[1:-1]
housing_n['zipcode'] = housing_n['zipcode'].str[1:-1]
housing_n['date'] = housing_n['date'].apply(lambda x: x.replace(x, x[0:10]))
housing = housing_n.convert_objects(convert_numeric=True)
housing['sqm_living'] = round(housing['sqft_living'] / valueOfSqM)
housing['sqm_lot'] = round(housing['sqft_lot'] / valueOfSqM)
housing['sqm_above'] = round(housing['sqft_above'] / valueOfSqM)
housing['sqm_basement'] = round(housing['sqft_basement'] / valueOfSqM)
housing = housing.drop(["sqft_living", "sqft_lot", "sqft_above", "sqft_basement"], axis=1)
housing['date'] = housing['date'].apply(lambda x: x.replace(x, x[1:5] + "-" + x[5:7] + "-" + x[7:9]))
housing['date'] = housing['date'].apply(lambda x: datetime.datetime.strptime(x, "%Y-%m-%d").date())


def create_price_grade_chart():
    groupByGrade = housing[['price', 'grade']].groupby(['grade']).mean()
    legend_title = "House grades"
    groupByGrade['angle'] = groupByGrade['price'] / groupByGrade['price'].sum() * 2 * pi
    groupByGrade['color'] = Category20c[len(groupByGrade.index)]
    groupByGrade['index'] = groupByGrade.index
    p1 = figure( title="Average price of houses depending on grade",
                toolbar_location=None, tools='hover', sizing_mode="scale_width")
    p1.ygrid.grid_line_color = None
    p1.xaxis.visible = False
    p1.yaxis.visible = False
    p1.toolbar.logo=None
    p1.toolbar_location= None
    p1.wedge(x=0, y=1, radius=0.4, start_angle=cumsum('angle', include_zero=True),
             end_angle=cumsum('angle'), line_color="black", fill_color='color',
             legend='grade', source=groupByGrade)
    hover = p1.select(dict(type=HoverTool))
    hover.tooltips = [('Average price', '@price{0,0}$'), ('Grade', '@grade')]
    tab1 = Panel(child=p1, title='Grade')
    return tab1


# def create_location_chart():
#     housing['coordinates_x'] = ""
#     housing['coordinates_y'] = ""
#     for i in range(len(housing)):
#         housing['coordinates_x'].iloc[i] = merc(housing['lat'].iloc[i], housing['long'].iloc[i])[0]
#         housing['coordinates_y'].iloc[i] = merc(housing['lat'].iloc[i], housing['long'].iloc[i])[1]
#     p2 = figure(x_axis_type="mercator", y_axis_type="mercator")
#     p2.add_tile(CARTODBPOSITRON)
#     p2.circle(x=housing['coordinates_x'], y=housing['coordinates_y'],  line_color="#FF0000",
#              fill_color="#FF0000", fill_alpha=0.05)
#     tab2 = Panel(child=p2, title='Square meters')
#     return tab2


def create_condition_chart():
    condition = housing[['condition']].sort_values(by='condition')
    t = pd.DataFrame(condition['condition'].value_counts())
    t['index'] = t.index
    t['index'] = t['index'].astype(str)
    t['condition'] = t['condition'].astype(str)
    data_dict = {'x': t['index'], 'y': t['condition']}
    source = ColumnDataSource(data=data_dict)
    p3 = figure(plot_height=300, sizing_mode="scale_width", x_range=data_dict['x'],  title='Number of houses in various conditions',
                tools ="wheel_zoom,reset")
    p3.vbar(x='x', top='y', source=source, width=0.7)
    p3.add_tools(HoverTool(tooltips=[('Value', '@y{int}')]))
    p3.xaxis.axis_label = "Conditions"
    p3.yaxis.axis_label = "Number of houses"
    p3.toolbar.autohide = True
    p3.xgrid.grid_line_color = None
    p3.y_range.start = 0
    tab3 = Panel(child=p3, title="Conditions")
    return tab3


def create_square_meters_chart():
    group_by_floors = housing[['sqm_living', 'sqm_above', 'sqm_basement', 'sqm_lot', 'floors']].groupby(['floors']).mean()
    group_by_floors['index'] = group_by_floors.index
    data_dict = {'x': group_by_floors['index'], 'living': group_by_floors['sqm_living'],
                 'above': group_by_floors['sqm_above'],
                 'basement': group_by_floors['sqm_basement'], 'lot': group_by_floors['sqm_lot']}
    source = ColumnDataSource(data=data_dict)
    p4 = figure(plot_height=500, plot_width=1200,  sizing_mode="scale_width",tools ="wheel_zoom,reset")
    l1 = p4.line(source=source, x='x', y='lot', line_width=2, line_color="#FB9A99")
    l2 = p4.line(source=source, x='x', y='basement', line_width=2, line_color="#33A02C")
    l3 = p4.line(source=source, x='x', y='above', line_width=2, line_color="#B2DF8A")
    l4 = p4.line(source=source, x='x', y='living', line_width=2, line_color="#A6CEE3")
    hover1 = HoverTool(renderers=[l1], tooltips=[('Floor', '@x{0.0,0}'), ('Value', '@lot{0.0}')])
    hover2 = HoverTool(renderers=[l2], tooltips=[('Floor', '@x{0.0,0}'), ('Value', '@basement{0.0}')])
    hover3 = HoverTool(renderers=[l3], tooltips=[('Floor', '@x{0.0,0}'), ('Value', '@above{0.0}')])
    hover4 = HoverTool(renderers=[l4], tooltips=[('Floor', '@x{0.0,0}'), ('Value', '@living{0.0}')])
    p4.add_tools(hover1, hover2, hover3, hover4)
    p4.toolbar.autohide = True
    p4.xaxis.axis_label = "Number of floors"
    p4.yaxis.axis_label = "Average square meters"
    legend = Legend(items=[
        ('Average square meters lot', [l1]),
        ('Average square meters basement', [l2]),
        ('Average square meters above', [l3]),
        ('Average square meters living', [l4])], location='center')

    legend.click_policy = 'hide'
    p4.add_layout(legend, 'right')

    layout_ = column(p4)
    tab4 = Panel(child=layout_, title='Floors and square area')
    return tab4


def create_zip_code_chart():
    group_by_zipcode = housing[['zipcode', 'price']].groupby(['zipcode']).mean().sort_values(by='price', ascending=False)[
                     0:10]
    group_by_zipcode['zipcode'] = group_by_zipcode.index
    group_by_zipcode['price'] = group_by_zipcode['price'].astype(str)
    group_by_zipcode['zipcode'] = group_by_zipcode['zipcode'].astype(str)
    data_dict = {'x': group_by_zipcode['zipcode'], 'y': group_by_zipcode['price']}
    p5 = figure(plot_height=300, sizing_mode="scale_width",
                x_range=data_dict['x'],
                title='Top 10 most richest average neighbourhoods')
    p5.vbar(source= data_dict, x='x', top='y', width=0.7)
    p5.left[0].formatter.use_scientific= False
    p5.add_tools(HoverTool(tooltips=[("Zipcode", "@x"), ('Average price', '@y{0.0}')]))
    p5.xgrid.grid_line_color = None
    p5.y_range.start = 0
    tab5 = Panel(child=p5, title='Most expensive neighbourhoods')
    return tab5

def create_renovated_chart():
    group_by_renovated = housing[['yr_renovated', 'price']].groupby(['yr_renovated']).count()
    group_by_renovated['index'] = group_by_renovated.index
    number_of_not_renovated = group_by_renovated.where(group_by_renovated['index'] == 0)['price'].sum().sum()
    number_of_renovated = group_by_renovated.where(group_by_renovated['index'] > 0)['price'].sum().sum()
    dataframe = pd.DataFrame([['Renovated', number_of_renovated], ['Not renovated', number_of_not_renovated]],
                             columns=['type', 'number'])
    dataframe['angle'] = dataframe['number'] / dataframe['number'].sum() * 2 * pi

    dataframe['color'] = ['green', 'orange']
    p6 = figure(plot_height=300, title="Number of renovated and not renovated houses", toolbar_location=None,
                tools='hover')
    p6.xgrid.grid_line_color = None
    p6.ygrid.grid_line_color = None
    p6.xaxis.visible = False
    p6.yaxis.visible = False
    p6.wedge(x=0, y=1, radius=0.4, start_angle=cumsum('angle', include_zero=True),
             end_angle=cumsum('angle'), line_color="black", fill_color='color',
             legend='type', source=dataframe)
    p6.sizing_mode = 'scale_width'
    hover = p6.select(dict(type=HoverTool))
    hover.tooltips = [('Number of houses', '@number{int}')]
    tab6 = Panel(child=p6, title='Renovation')
    return tab6


def create_date_price_count_chart():
    # seventh
    groupByDate = housing[['date', 'price']].groupby(['date']).count()
    groupByDate['index'] = groupByDate.index
    p7 = figure(plot_height=300, x_axis_type='datetime')
    p7.line(groupByDate['index'], groupByDate['price'], line_width=2, color="#A6CEE3",
            legend='Number of sold houses')
    p7.add_tools(HoverTool(tooltips=[("Date", "@x{%F}"), ('Sold houses', '@y{int}')],
                           formatters={'x': 'datetime'}))
    p7.sizing_mode = 'scale_width'

    tab7 = Panel(child=p7, title='Sold houses')
    return tab7

def create_date_price_sum_chart():
    groupByPrice = housing[['date', 'price']].groupby(['date']).sum()
    groupByPrice['index'] = groupByPrice.index
    p8 = figure(plot_height=300,  x_axis_type='datetime')
    p8.yaxis.formatter = BasicTickFormatter(use_scientific=False)

    p8.line(groupByPrice['index'], groupByPrice['price'], line_width=2, color="#33A02C",
            legend='Earned money')
    p8.add_tools(HoverTool(tooltips=[("Date", "@x{%F}"), ('Income', '@y{0.0,0}$')],
                           formatters={'x': 'datetime'}))
    p8.sizing_mode = 'scale_width'
    # source = ColumnDataSource(data=dict(x=groupByPrice['date'], y=groupByPrice['price']))
    tab8 = Panel(child=p8, title='Houses income')
    return tab8


def make_diagrams():
    tabs = Tabs(tabs=[create_price_grade_chart()],sizing_mode="scale_width")
    script, div = components(tabs)
    return script, div


