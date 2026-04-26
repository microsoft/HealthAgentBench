# Workspace — Report Generation

- `benchmark_tasks.json`: task definition with patient history and target study info
- `submission.json`: editable; fill in `final_answer` with generated report

Patient data is mounted at `/data/patient/` as timestamped folders:

    /data/patient/
      manifest.json                        # study index
      <timestamp>_s<study_id>/             # one folder per study, chronological
        <dicom_id>.jpg                     # chest X-ray image(s)
        report.txt                         # radiology report (PRIOR studies only)

The target study's folder contains only `.jpg` images — no `report.txt`.

Patient: 13067703
Target study: 57241942
Prior studies: 9
