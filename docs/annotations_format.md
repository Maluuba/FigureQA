# FigureQA: Annotations Data Schema

## Overview

```
[   # A list of "annotation objects"
    {
         "type":                # Figure type. 
                                # One of ["vbar_categorical", "hbar_categorical",  "pie", "line", "dot_line"]

         "general_plot_data":   # Annotation data for general figure elements.
                                # E.g. dimensions, axes, labels, legend, etc.

         "models":              # A list of annotations per plot element. Structure depends on figure type.

         "image_index":         # Unique identifier for the source image. Image is at "png/<image_index>.png".
    },
    ...
]
```


## General Notes

- "color(s)" are the hex values of the colors, whereas "label(s)" are the color names.
- "name" and "label(s)" fields in a "models" object correspond to the color name (i.e. "color(1|2)_name" in the qa_pairs.json file).
- In "bbox(es)", "x", "y", "w", and "h" are pixel coordinates, where y=0 means the top of the figure.
- Other fields are source data for generating the figure.


## Annotations Object Structure Details

```
COMMON ======================================================

"type": "" # One of ["vbar_categorical", "hbar_categorical",  "pie", "line", "dot_line"]

"image_index": Int

"models": [{}]

"general_figure_info": {
    "figure_info": {
        "bbox": {"x": Int, "y": Int, "w": Int, "h": Int}
    },
    "plot_info": {
        "bbox": {"x": Int, "y": Int, "w": Int, "h": Int}
    },
    "x_axis": {
        "major_ticks": {
            "bboxes": [{"x": Int, "y": Int, "w": Int, "h": Int}, ...],
            "values": [Float, ...] OR [Int, ...]
        },
        "minor_ticks": {
            "bboxes": [{"x": Int, "y": Int, "w": Int, "h": Int}, ...],
            "values": [Float, ...] OR [Int, ...]
        },
        "major_labels": {
            "bboxes": [{"x": Int, "y": Int, "w": Int, "h": Int}, ...],
            "values": ["", ...]
        },
        "rule": {
            "bbox": {"x": Int, "y": Int, "w": Int, "h": Int}
        },
        "label": {
            "bbox": {"x": Int, "y": Int, "w": Int, "h": Int}
            "text": ""
        }

    },
    "y_axis": {
        "major_ticks": {
            "bboxes": [{"x": Int, "y": Int, "w": Int, "h": Int}, ...],
            "values": [Float, ...] OR [Int, ...]
        },
        "minor_ticks": {
            "bboxes": [{"x": Int, "y": Int, "w": Int, "h": Int}, ...],
            "values": [Float, ...] OR [Int, ...]
        },
        "major_labels": {
            "bboxes": [{"x": Int, "y": Int, "w": Int, "h": Int}, ...]
            "values": ["", ...]
        },
        "rule": {
            "bbox": {"x": Int, "y": Int, "w": Int, "h": Int}
        },
        "label": {
            "bbox": {"x": Int, "y": Int, "w": Int, "h": Int},
            "text": ""
        }

    },
    "x_grid_lines": {
        "bboxes": [{"x": Int, "y": Int, "w": Int, "h": Int}, ...],
        "values": [Float, ...]
    },
    "y_grid_lines": {
        "bboxes": [{"x": Int, "y": Int, "w": Int, "h": Int}, ...],
        "values": [Float, ...]
    },
    "title": {
        "bbox": {"x": Int, "y": Int, "w": Int, "h": Int}
        "text": ""
    },
    "legend": {
        "bbox": {"x": Int, "y": Int, "w": Int, "h": Int},
        "items": [
            {
                "model": "", # Name of the plot element that the legend item corresponds to
                             # i.e. "color(1|2)_name" in the qa_pairs.json
                "label": {
                    "bbox": {"x": Int, "y": Int, "w": Int, "h": Int},
                    "text": ""
                },
                "preview": {
                    "bbox": {"x": Int, "y": Int, "w": Int, "h": Int},
                }
            }
        ]
    }
}


FOR SPECIFIC FIGURES ============================================================


LINE PLOT -------------------

Notes:
- "bboxes" are for segments, and therefore are not aligned with "x", "y", "labels", "colors"

"models": [
    {
        "name": "", # Plot element identifier, in this case color name, i.e. "color(1|2)_name" in the qa_pairs.json file
        "bboxes": [{"x": Int, "y": Int, "w": Int, "h": Int}, ...], 
        "x":      [Float, ...],
        "y":      [Float, ...],
        "label": "",
        "color": "",
    },
    ...
]


DOT LINE PLOT -------------------

"models": [
    {
        "name": "", # Plot element identifier, in this case color name, i.e. "color(1|2)_name" in the qa_pairs.json file
        "bboxes": [{"x": Int, "y": Int, "w": Int, "h": Int}, ...],
        "x":      [Float, ...],
        "y":      [Float, ...],
        "label": "",
        "color": ""
    },
    ...
]


PIE PLOT -------------------

Notes:
- One model per slice

"models": [
    {
        "name": "", # Plot element identifier, in this case color name, i.e. "color(1|2)_name" in the qa_pairs.json file
        "bbox": {"x": Int, "y": Int, "w": Int, "h": Int}
        "span":  Float, # Radians
        "start": Float, # Radians
        "end":   Float, # Radians
        "label": "",
        "color": "",
    },
    ...
]

CATEGORICAL BAR PLOT -------------------

Notes:

- Only one object element encompassing data for all bars
- Bar identifiers are the "labels"
- "labels", "colors", "bboxes", "x", "y" are all aligned

"models": [ 
    {
        "name": "bars",
        "bboxes": [{"x": Int, "y": Int, "w": Int, "h": Int}, ...],
        "x":      [Float, ...] OR ["", ...], # former is horizontal bar, latter is vertical bar
        "y":      ["", ...] OR [Float, ...], # former is horizontal bar, latter is vertical bar
        "labels": ["", ...], # All plot element identifiers, i.e. "color(1|2)_name" in the qa_pairs.json file
        "colors": ["", ...], 
        "width":  Float
    }
]
```