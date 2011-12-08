from django.db import models
from django.contrib import admin
from lxml import etree

# Create your models here.

class XMLParseError(Exception): pass
class TableTypeError(Exception): pass
class GlobalNameError(Exception): pass

def create_model(name, fields=None, app_label='', module='', options=None, admin_opts=None):
    """
    Create specified model
    """
    class Meta:
        # Using type('Meta', ...) gives a dictproxy error during model creation
        pass

    if app_label:
        # app_label must be set using the Meta inner class
        setattr(Meta, 'app_label', app_label)

    # Update Meta with any options that were provided
    if options is not None:
        for key, value in options.iteritems():
            setattr(Meta, key, value)

    # Set up a dictionary to simulate declarations within a class
    attrs = {'__module__': module, 'Meta': Meta}

    # Add in any fields that were provided
    if fields:
        attrs.update(fields)

    # Create the class, which automatically triggers ModelBase processing
    model = type(name, (models.Model,), attrs)

    # Create an Admin class if admin options were provided
    if admin_opts is not None:
        class Admin(admin.ModelAdmin):
            pass
        for key, value in admin_opts:
            setattr(Admin, key, value)
        admin.site.register(model, Admin)

    return model

def raiser(message):
    raise XMLParseError(message)

def parse_xml():
    
    f=open('dyn_model/model.xml', 'r')
    xml_data = f.read()
    f.close()

    root = etree.fromstring(xml_data)
    model_dict = {}
    
    for xml_model in root.iter('DjangoApp'):
	for table in xml_model:
	    t_name = table.get('name')
	    if not t_name: 
		raiser("Table 'name' attr does not exists")
	    
	    fields = {}
	    options = {}
	    
	    for column in table:
		c_name = column.get('name')
		if not c_name:
		    raiser("Column 'name' attr does not exists")
		
		c_type = column.get('type')
		if not c_type:
		    raiser("Column 'type' attr does not exists")
		
		model_field = None

		if c_type == 'char':
		    max_length = column.get('max_length', 255)
	    	    model_field = models.CharField(max_length=max_length)
		elif c_type == 'int':
	    	    model_field = models.IntegerField()
	    	elif c_type == 'date':
	    	    model_field = models.DateField()
	    	elif c_type == 'text':
	    	    model_field = models.TextField()
	    	else:
	    	    raise TableTypeError("Table does not support '%s' type" % c_type)
	    	#TODO:
	    	#elif other types
	    	
	    	model_field._is_model = True
		fields[c_name] = model_field
	
	    __str__ = lambda self, attrs=fields: ' '.join([str(getattr(self, attr)) for attr in attrs if attr != '__str__'])
	    fields['__str__'] = __str__
	
	    admin_opts = {} if table.get('admin') else None
	    
	    verbose_name = table.get('title')
	    if verbose_name: 
		options['verbose_name'] = verbose_name
		options['verbose_name_plural'] = verbose_name
		
	    if t_name in globals():
		raise GlobalNameError("Duplicate table name '%s'" % t_name)
	    
	    #For import models by table name
	    globals()[t_name] = create_model(t_name, fields, app_label='dyn_model', 
				options=options, admin_opts=admin_opts)

parse_xml()
