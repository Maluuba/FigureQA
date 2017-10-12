# JSON + PNG Generation Format

## Without the combiner script

After using the `figure_generation.py` script.

```
<generation_root>/
    png/
        <id>_<type>.png
        ...
    json_qa/
        <id>_<type>.json
        ...
    json_annotations/
        <id>_<type>_annotations.json
        ...
```

## With the combiner script

After using the `json_combiner.py` script.

```
<combination_root>/
    png/
        <image_index>.png
        ...
    qa_pairs.json
    annotations.json
```

### qa_pairs.json Structure

```
{
    "qa_pairs": [
        {
            "question_string":          "...",
            "question_id":              Int,
            "answer":                   [0, 1],
            "color1_name":              "...",
            "color1_id":                Int,
            "color1_rgb":               [ [0-255], [0-255], [0-255] ],
            "color2_name":              "...",                          OR "--None--" if not applicable
            "color2_id":                Int,                            OR -1 if not applicable
            "color2_rgb":               [ [0-255], [0-255], [0-255] ],  OR [-1, -1, -1] if not applicable
            "image_index":              Int, // image file name is "png/<image_index>.png"
        },
        ...
    ],
    "total_distinct_questions": Int, // For whole dataset, defines dimension of encoded question vector
    "total_distinct_colors":    Int  // For whole dataset, defines dimension of encoded question vector
}
```

### Annotation JSON Structure

See `annotations_format.md`
