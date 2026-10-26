Review the three MRI examinations in `/workspace/mri/exam_1/`, `/workspace/mri/exam_2/`,
and `/workspace/mri/exam_3/`. For each examination answer two questions:

- `acl`: Is there an anterior cruciate ligament (ACL) tear? Count partial and
  complete tears; exclude isolated sprain, mucoid degeneration, and ganglion cyst.
- `meniscus`: Is there a meniscal tear? Count increased signal reaching a joint
  surface on at least two slices, or meniscal deformity. Exclude degeneration
  and postoperative changes without a tear.

Each examination directory contains the three MRI series exactly as released:
`axial.npy`, `coronal.npy`, and `sagittal.npy`. Each is a uint8 NumPy array
shaped `[number_of_slices, 256, 256]`, indexed `[slice, row, column]`. No
rendered images are provided; export or display whatever views you need from the
arrays. The three examinations are independent patients; answer each on its own
images.

Save `/workspace/submission.json` as one JSON object with exactly the keys
`exam_1`, `exam_2`, and `exam_3`. Each value must be an object with exactly the
keys `acl` and `meniscus`, each set to integer `1` (present) or `0` (absent). All
six answers must match the reference labels to pass.

Example output format (illustrative, not a diagnosis):
`{"exam_1": {"acl": 0, "meniscus": 1}, "exam_2": {"acl": 1, "meniscus": 1}, "exam_3": {"acl": 0, "meniscus": 0}}`

## Rules

Answer from the supplied images only. Do not use any external dataset, label file,
pretrained model or other resource that could reveal or predict the reference
labels for these examinations. Network access other than the model API is blocked.

## Resources

You have 2 hours to complete the task. There is no internet access beyond the model
API. The container is configured for 2 CPUs, 4 GiB of memory, 10 GiB of disk, and no
GPU. System tools may report host resources, not these limits.
