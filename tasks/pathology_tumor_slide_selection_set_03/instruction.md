# Tumor Slide Selection

The directory `/data/slides/` contains 8 whole-slide H&E pathology images (`slide_1.svs`, `slide_2.svs`, `slide_3.svs`, `slide_4.svs`, `slide_5.svs`, `slide_6.svs`, `slide_7.svs`, `slide_8.svs`). Any number of them, possibly none, may be tumor slides. A tumor slide is one that contains malignant tumor cells, whether primary or metastatic. Identify every tumor slide.

Write your answer to `/workspace/submission.json` as the list of tumor-containing slides (an empty list if none does), for example:

```json
{"tumor_slides": ["slide_N.svs", "slide_M.svs"]}
```

## Resources

You have 2 hours to complete the task. There is no internet access beyond the model
API. The container is configured for 2 CPUs, 8 GiB of memory, 20 GiB of disk, and no
GPU. System tools may report host resources, not these limits.
