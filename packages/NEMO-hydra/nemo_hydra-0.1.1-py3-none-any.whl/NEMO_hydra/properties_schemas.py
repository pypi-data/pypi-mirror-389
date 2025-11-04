# This can be extended in settings.py
TOOL_PROPERTIES_JSON_SCHEMA = {
    "type": "object",
    "required": ["tool_categories", "supported_sample_size", "permitted_materials", "prohibited_materials"],
    "properties": {
        "tool_categories": {
            "title": "Tool Category/Type",
            "type": "array",
            "uniqueItems": True,
            "items": {
                "anyOf": [
                    {
                        "title": "Deposition",
                        "type": "string",
                        "enum": [
                            "Atomic layer deposition (ALD)",
                            "Chemical vapor deposition (CVD)",
                            "Physical vapor deposition (PVD)",
                        ],
                    },
                    {
                        "title": "Lithography",
                        "type": "string",
                        "enum": ["Photolithography", "E-beam Lithography", "3D Lithography"],
                    },
                    {
                        "title": "Etch",
                        "type": "string",
                        "enum": ["RIE", "ICP", "DRIE", "Asher", "Wet etch"],
                    },
                    {
                        "title": "Thermal Processing",
                        "type": "string",
                        "enum": ["Diffusion", "Rapid thermal anneal (RTA)", "Oxidation", "Annealing"],
                    },
                    {
                        "title": "Wet Processing",
                        "type": "string",
                        "enum": ["Solvent", "Acid", "Developer"],
                    },
                    {
                        "title": "Imaging/Metrology",
                        "type": "string",
                        "enum": [
                            "Scanning probe microscopy (including AFM, SPM)",
                            "Electron microscopy",
                            "Magnetic materials characterization",
                            "Optical microscopy and spectroscopy",
                            "Surface analysis",
                            "X-ray diffraction and imaging",
                            "Electrical test",
                        ],
                    },
                    {
                        "title": "Packaging",
                        "type": "string",
                        "enum": [
                            "Dice",
                            "Bonding",
                            "Wirebonding",
                        ],
                    },
                ],
            },
        },
        "supported_sample_size": {
            "title": "Supported Sample Size",
            "type": "array",
            "uniqueItems": True,
            "items": {
                "type": "string",
                "enum": ["300mm", "200mm", "150mm", "100mm or smaller", "Pieces / coupons", "Other"],
            },
        },
        "permitted_materials": {
            "title": "Permitted Materials",
            "type": "array",
            "items": {"$ref": "#/$defs/materials"},
        },
        "prohibited_materials": {
            "title": "Prohibited Materials",
            "type": "array",
            "items": {"$ref": "#/$defs/materials"},
        },
    },
    "$defs": {
        "materials": {
            "type": "object",
            "properties": {
                "name": {"title": "Name", "type": "string", "minLength": 1},
                "symbol": {"title": "Symbol", "type": "string"},
                "type": {
                    "title": "Type",
                    "type": "string",
                    "enum": [
                        "Substrate",
                        "Exposed film",
                        "Required surface film",
                        "Buried film",
                        "Removed film",
                        "Never used",
                    ],
                },
                "qualifier": {
                    "title": "Qualifier",
                    "type": "string",
                    "help_text": "For example maximum area %, maximum detectable concentration on wafer etc.",
                },
            },
        }
    },
}
