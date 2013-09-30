{
    "origin" : {
        "title" : "origin",
        "help_text" : "Origin",
        "fields" : [
            {
                "field_name" : "place_of_origin",
                "field_type": "string",
                "help_text": "Place of origin",
                "blank": True,
                "default": None,
                "nullable": True,
                "readonly": False,
                "unique": False
                },
            {
                "field_name" : "date_of_origin",
                "field_type": "string",
                "help_text": "Date of origin",
                "blank": True,
                "default": None,
                "nullable": True,
                "readonly": False,
                "unique": False
                }
            ]
        },
    "additional_notes" : {
        "title": "additional_notes",
        "help_text": "Additional Notes",
        "fields" : [
            {
                "field_name" : "note",
                "field_type": "string",
                "help_text": "Notatka",
                "blank": True,
                "default": None,
                "nullable": True,
                "readonly": False,
                "unique": False
                }
            ]
        },
    "bibliographic_citation" : {
        "title" : "bibliographic_citation",
        "help_text" : "Bibliographic Citation",
        "fields" : [
            {
                "field_name" : "author",
                "field_type": "string",
                "blank": True,
                "default": None,
                "help_text": "Author",
                "nullable": True,
                "readonly": False,
                "unique": False
                },
            {
                "field_name" : "source",
                "blank": True,
                "default": None,
                "help_text": "Source",
                "nullable": True,
                "readonly": False,
                "field_type": "string",
                "unique": False
                },
            {
                "field_name" : "scope_of_citation",
                "blank": True,
                "default": None,
                "help_text": "Scope of Citation",
                "nullable": True,
                "readonly": False,
                "field_type": "string",
                "unique": False
                },
            {
                "field_name" : "place_of_publishing",
                "blank": True,
                "default": None,
                "help_text": "Place of Publishing",
                "nullable": True,
                "readonly": False,
                "field_type": "string",
                "unique": False
                },
            {
                "field_name" : "date_of_publishing",
                "blank": True,
                "default": None,
                "help_text": "Date of Publishing",
                "nullable": True,
                "readonly": False,
                "field_type": "string",
                "unique": False
                },
            ]
        },
    "accompanying_material" : {
        "title" : "accompanying_material",
        "help_text" : "Dodatkowe materialy",
        "fields" : [
            {
                "field_name" : "description",
                "blank": False,
                "default": '',
                "help_text": "Opis",
                "nullable": True,
                "readonly": False,
                "field_type": "string",
                "unique": False
                },
            {
                "field_name" : "bibliographic_citation",
                "blank": False,
                "default": None,
                "help_text": "Cytate bibliograficzne",
                "nullable": True,
                "readonly": False,
                "unique": False,
                "field_type": "embeddeddocument",
                "embedded_section" : "$bibliographic_citation"
                }
            ]        
        }
    }
