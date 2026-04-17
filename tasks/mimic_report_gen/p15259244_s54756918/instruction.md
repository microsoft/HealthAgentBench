# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `15259244`
- 43 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `54756918`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 58008930
- **Date:** 2125-01-10 21:05:52
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2125-01-10_21-05-52_s58008930/`
- **Report:** `/data/patient/2125-01-10_21-05-52_s58008930/report.txt`
- **Images:** `/data/patient/2125-01-10_21-05-52_s58008930/35b21042-72d1e131-7566b7a8-5f8005c0-b27fc76d.jpg`

### Prior Study 2: 52794954
- **Date:** 2125-01-11 17:50:19
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2125-01-11_17-50-19_s52794954/`
- **Report:** `/data/patient/2125-01-11_17-50-19_s52794954/report.txt`
- **Images:** `/data/patient/2125-01-11_17-50-19_s52794954/52e6e293-df5b1b69-a7d263ca-5400f4b2-f5c41027.jpg`

### Prior Study 3: 50243155
- **Date:** 2125-01-13 07:27:20
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2125-01-13_07-27-20_s50243155/`
- **Report:** `/data/patient/2125-01-13_07-27-20_s50243155/report.txt`
- **Images:** `/data/patient/2125-01-13_07-27-20_s50243155/3920cf42-8cd1362b-cbe6eaee-518b1fa6-a7358a5b.jpg`

### Prior Study 4: 54251102
- **Date:** 2125-01-29 05:11:52
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2125-01-29_05-11-52_s54251102/`
- **Report:** `/data/patient/2125-01-29_05-11-52_s54251102/report.txt`
- **Images:** `/data/patient/2125-01-29_05-11-52_s54251102/c9f72311-636e3e48-e91cc14d-ba98d9ce-c823252f.jpg`

### Prior Study 5: 59671026
- **Date:** 2125-01-30 13:17:29
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2125-01-30_13-17-29_s59671026/`
- **Report:** `/data/patient/2125-01-30_13-17-29_s59671026/report.txt`
- **Images:** `/data/patient/2125-01-30_13-17-29_s59671026/87694c3c-e07ea01b-0ee35fd8-55a7defd-8e318d65.jpg`

### Prior Study 6: 52824127
- **Date:** 2125-01-30 19:13:06
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2125-01-30_19-13-06_s52824127/`
- **Report:** `/data/patient/2125-01-30_19-13-06_s52824127/report.txt`
- **Images:** `/data/patient/2125-01-30_19-13-06_s52824127/8312c3a4-f0043050-3db9e48c-8b180ed0-faf4d335.jpg`

### Prior Study 7: 54912258
- **Date:** 2125-02-01 02:24:21
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2125-02-01_02-24-21_s54912258/`
- **Report:** `/data/patient/2125-02-01_02-24-21_s54912258/report.txt`
- **Images:** `/data/patient/2125-02-01_02-24-21_s54912258/2241b085-d8b05d1d-b5f91fce-e5b5e662-4e27dbc6.jpg`

### Prior Study 8: 56723838
- **Date:** 2125-02-02 02:16:27
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2125-02-02_02-16-27_s56723838/`
- **Report:** `/data/patient/2125-02-02_02-16-27_s56723838/report.txt`
- **Images:** `/data/patient/2125-02-02_02-16-27_s56723838/28674cfd-a09cd562-c2ee2007-8a9a2145-bc7be12c.jpg`

### Prior Study 9: 53282268
- **Date:** 2125-02-16 12:52:47
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2125-02-16_12-52-47_s53282268/`
- **Report:** `/data/patient/2125-02-16_12-52-47_s53282268/report.txt`
- **Images:** `/data/patient/2125-02-16_12-52-47_s53282268/e71f51f3-72341a6f-e930d575-66d2c3ef-339886c5.jpg`

### Prior Study 10: 53532692
- **Date:** 2125-03-03 00:15:48
- **Procedure:** CHEST (PA AND LAT)
- **Views:** PA, LATERAL
- **Folder:** `/data/patient/2125-03-03_00-15-48_s53532692/`
- **Report:** `/data/patient/2125-03-03_00-15-48_s53532692/report.txt`
- **Images:** `/data/patient/2125-03-03_00-15-48_s53532692/bb03b651-512952bc-0ea27cd3-c61b8255-0b80bbb5.jpg`, `/data/patient/2125-03-03_00-15-48_s53532692/d1badba1-e01afe43-80c374ea-e81e55b3-ae48bd8a.jpg`

### Prior Study 11: 50758061
- **Date:** 2125-03-25 21:19:29
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2125-03-25_21-19-29_s50758061/`
- **Report:** `/data/patient/2125-03-25_21-19-29_s50758061/report.txt`
- **Images:** `/data/patient/2125-03-25_21-19-29_s50758061/43042279-0b8f5bb0-a45d17b6-f8d3b29f-0c787952.jpg`

### Prior Study 12: 58464159
- **Date:** 2125-03-26 09:15:32
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2125-03-26_09-15-32_s58464159/`
- **Report:** `/data/patient/2125-03-26_09-15-32_s58464159/report.txt`
- **Images:** `/data/patient/2125-03-26_09-15-32_s58464159/93c7dad2-501ec9ee-b423b86d-71f2b828-1e3f0573.jpg`

### Prior Study 13: 59654440
- **Date:** 2125-03-27 15:35:18
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2125-03-27_15-35-18_s59654440/`
- **Report:** `/data/patient/2125-03-27_15-35-18_s59654440/report.txt`
- **Images:** `/data/patient/2125-03-27_15-35-18_s59654440/981f5956-9dbb9f69-8b7bbf12-b872f7a3-16f09cf4.jpg`

### Prior Study 14: 59963711
- **Date:** 2125-04-08 14:57:29
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2125-04-08_14-57-29_s59963711/`
- **Report:** `/data/patient/2125-04-08_14-57-29_s59963711/report.txt`
- **Images:** `/data/patient/2125-04-08_14-57-29_s59963711/bcb39e0c-aa48bfc8-50a5f824-1f4b73e1-4a1f3235.jpg`

### Prior Study 15: 51427308
- **Date:** 2125-04-08 18:24:54
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2125-04-08_18-24-54_s51427308/`
- **Report:** `/data/patient/2125-04-08_18-24-54_s51427308/report.txt`
- **Images:** `/data/patient/2125-04-08_18-24-54_s51427308/cd20a77e-2332eb46-6c09f2d2-e0e8d1d9-8f18baf1.jpg`

### Prior Study 16: 51299369
- **Date:** 2125-04-09 21:20:29
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2125-04-09_21-20-29_s51299369/`
- **Report:** `/data/patient/2125-04-09_21-20-29_s51299369/report.txt`
- **Images:** `/data/patient/2125-04-09_21-20-29_s51299369/bd1321c9-fbaf9718-c06fef48-a5c3ccaa-5d48ccd1.jpg`

### Prior Study 17: 57867628
- **Date:** 2125-04-11 07:21:53
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2125-04-11_07-21-53_s57867628/`
- **Report:** `/data/patient/2125-04-11_07-21-53_s57867628/report.txt`
- **Images:** `/data/patient/2125-04-11_07-21-53_s57867628/88d66a2e-11751a81-a9daf8df-433b48ec-34cd1570.jpg`

### Prior Study 18: 54007778
- **Date:** 2125-04-12 07:40:42
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2125-04-12_07-40-42_s54007778/`
- **Report:** `/data/patient/2125-04-12_07-40-42_s54007778/report.txt`
- **Images:** `/data/patient/2125-04-12_07-40-42_s54007778/c249e803-7af4d888-0de68b91-d6fda68a-387c0f5d.jpg`

### Prior Study 19: 50903359
- **Date:** 2125-04-13 10:35:07
- **Procedure:** Performed Desc
- **Views:** LL, LL, PA
- **Folder:** `/data/patient/2125-04-13_10-35-07_s50903359/`
- **Report:** `/data/patient/2125-04-13_10-35-07_s50903359/report.txt`
- **Images:** `/data/patient/2125-04-13_10-35-07_s50903359/25caadda-50ddd24f-cf51cc5a-25c4f090-e4d32c64.jpg`, `/data/patient/2125-04-13_10-35-07_s50903359/382f361b-7412dee4-3a5c243f-b3c792e4-d7f75a6f.jpg`, `/data/patient/2125-04-13_10-35-07_s50903359/4a9977bd-7c6765ff-7951cc3c-36666101-51dfc3fa.jpg`

### Prior Study 20: 54865295
- **Date:** 2125-04-16 22:11:19
- **Procedure:** 
- **Views:** AP
- **Folder:** `/data/patient/2125-04-16_22-11-19_s54865295/`
- **Report:** `/data/patient/2125-04-16_22-11-19_s54865295/report.txt`
- **Images:** `/data/patient/2125-04-16_22-11-19_s54865295/2f01c6ef-54b9b5f8-0f452502-c6cd3871-48a2c872.jpg`

### Prior Study 21: 58685714
- **Date:** 2125-04-17 12:17:01
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2125-04-17_12-17-01_s58685714/`
- **Report:** `/data/patient/2125-04-17_12-17-01_s58685714/report.txt`
- **Images:** `/data/patient/2125-04-17_12-17-01_s58685714/ecc315d7-39f7e590-405c1a1f-5a8f026d-560ba339.jpg`

### Prior Study 22: 56972683
- **Date:** 2125-04-17 20:04:04
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2125-04-17_20-04-04_s56972683/`
- **Report:** `/data/patient/2125-04-17_20-04-04_s56972683/report.txt`
- **Images:** `/data/patient/2125-04-17_20-04-04_s56972683/1b4e1f55-4fa1febf-abf7ed18-4531ddc4-2081f4ae.jpg`

### Prior Study 23: 58966181
- **Date:** 2125-04-21 09:14:06
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2125-04-21_09-14-06_s58966181/`
- **Report:** `/data/patient/2125-04-21_09-14-06_s58966181/report.txt`
- **Images:** `/data/patient/2125-04-21_09-14-06_s58966181/438f1b70-14b9e3c9-bd4e7c92-e6463ffc-e5aec56d.jpg`

### Prior Study 24: 50610932
- **Date:** 2125-04-25 10:41:00
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2125-04-25_10-41-00_s50610932/`
- **Report:** `/data/patient/2125-04-25_10-41-00_s50610932/report.txt`
- **Images:** `/data/patient/2125-04-25_10-41-00_s50610932/9ae19357-ed8ab74b-7c794e86-235ab6b4-b0b98b54.jpg`

### Prior Study 25: 57809151
- **Date:** 2125-05-02 18:00:07
- **Procedure:** 
- **Views:** PA
- **Folder:** `/data/patient/2125-05-02_18-00-07_s57809151/`
- **Report:** `/data/patient/2125-05-02_18-00-07_s57809151/report.txt`
- **Images:** `/data/patient/2125-05-02_18-00-07_s57809151/76ee4972-231e2314-e4e35ff5-8d2cd919-a98450dd.jpg`

### Prior Study 26: 54517823
- **Date:** 2125-06-17 21:49:46
- **Procedure:** CHEST (PA AND LAT)
- **Views:** AP
- **Folder:** `/data/patient/2125-06-17_21-49-46_s54517823/`
- **Report:** `/data/patient/2125-06-17_21-49-46_s54517823/report.txt`
- **Images:** `/data/patient/2125-06-17_21-49-46_s54517823/515703bc-4c8240a5-4b5d0a83-1f8c8dda-289ce799.jpg`

### Prior Study 27: 58869711
- **Date:** 2125-06-18 04:17:16
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2125-06-18_04-17-16_s58869711/`
- **Report:** `/data/patient/2125-06-18_04-17-16_s58869711/report.txt`
- **Images:** `/data/patient/2125-06-18_04-17-16_s58869711/995e2d81-54b60cfa-a52c5f7a-4d97f982-645e4731.jpg`

### Prior Study 28: 56650966
- **Date:** 2125-06-20 12:05:15
- **Procedure:** CHEST (PA AND LAT)
- **Views:** , LL
- **Folder:** `/data/patient/2125-06-20_12-05-15_s56650966/`
- **Report:** `/data/patient/2125-06-20_12-05-15_s56650966/report.txt`
- **Images:** `/data/patient/2125-06-20_12-05-15_s56650966/23b0575a-b419b472-1fd36614-eef44a94-f9e5c372.jpg`, `/data/patient/2125-06-20_12-05-15_s56650966/2eb98378-8832905d-f665c18e-f638be2d-e52c76f6.jpg`

### Prior Study 29: 50282926
- **Date:** 2125-07-08 23:03:47
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, AP
- **Folder:** `/data/patient/2125-07-08_23-03-47_s50282926/`
- **Report:** `/data/patient/2125-07-08_23-03-47_s50282926/report.txt`
- **Images:** `/data/patient/2125-07-08_23-03-47_s50282926/bba69ee7-df213de0-6bcebedd-77472984-0840a418.jpg`, `/data/patient/2125-07-08_23-03-47_s50282926/ede252ee-83066d8a-376961c0-b07de3b1-0dfeb1e0.jpg`

### Prior Study 30: 55259608
- **Date:** 2125-07-24 13:01:37
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2125-07-24_13-01-37_s55259608/`
- **Report:** `/data/patient/2125-07-24_13-01-37_s55259608/report.txt`
- **Images:** `/data/patient/2125-07-24_13-01-37_s55259608/6973b010-49ac25bb-d2e035bc-667938df-855b7f4c.jpg`

### Prior Study 31: 52697942
- **Date:** 2125-08-02 13:56:04
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2125-08-02_13-56-04_s52697942/`
- **Report:** `/data/patient/2125-08-02_13-56-04_s52697942/report.txt`
- **Images:** `/data/patient/2125-08-02_13-56-04_s52697942/928a3662-7a9bc2d9-1808833b-79fd5d7b-76aabf9d.jpg`

### Prior Study 32: 54770541
- **Date:** 2125-08-02 17:20:28
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2125-08-02_17-20-28_s54770541/`
- **Report:** `/data/patient/2125-08-02_17-20-28_s54770541/report.txt`
- **Images:** `/data/patient/2125-08-02_17-20-28_s54770541/b267e44d-493a0dca-420b4fd5-a91a1026-c3386cac.jpg`

### Prior Study 33: 54223010
- **Date:** 2125-08-05 02:57:10
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2125-08-05_02-57-10_s54223010/`
- **Report:** `/data/patient/2125-08-05_02-57-10_s54223010/report.txt`
- **Images:** `/data/patient/2125-08-05_02-57-10_s54223010/fd10e506-04541266-88f11cc7-b24b4822-8cf8bc4b.jpg`

### Prior Study 34: 51877138
- **Date:** 2125-08-20 14:34:42
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2125-08-20_14-34-42_s51877138/`
- **Report:** `/data/patient/2125-08-20_14-34-42_s51877138/report.txt`
- **Images:** `/data/patient/2125-08-20_14-34-42_s51877138/bbfadd26-26a1370d-69d5f8f9-5b210fd9-a89a0589.jpg`

### Prior Study 35: 51811172
- **Date:** 2125-09-13 23:03:56
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2125-09-13_23-03-56_s51811172/`
- **Report:** `/data/patient/2125-09-13_23-03-56_s51811172/report.txt`
- **Images:** `/data/patient/2125-09-13_23-03-56_s51811172/178a003a-0d5784da-664f8272-6c14ae7b-135dfadb.jpg`

### Prior Study 36: 53203970
- **Date:** 2125-10-03 18:03:10
- **Procedure:** CHEST (PA AND LAT)
- **Views:** AP, LATERAL
- **Folder:** `/data/patient/2125-10-03_18-03-10_s53203970/`
- **Report:** `/data/patient/2125-10-03_18-03-10_s53203970/report.txt`
- **Images:** `/data/patient/2125-10-03_18-03-10_s53203970/42fd3d74-fe3267e7-82ffa036-96225174-327660f6.jpg`, `/data/patient/2125-10-03_18-03-10_s53203970/650a92b6-c884c405-4d8cdb97-6cf12826-c8542d57.jpg`

### Prior Study 37: 52798218
- **Date:** 2125-10-06 09:36:47
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2125-10-06_09-36-47_s52798218/`
- **Report:** `/data/patient/2125-10-06_09-36-47_s52798218/report.txt`
- **Images:** `/data/patient/2125-10-06_09-36-47_s52798218/bc28ea67-0dc950d7-d5c81ea4-c8640ac1-e0a88e8d.jpg`

### Prior Study 38: 54437537
- **Date:** 2125-11-07 20:20:09
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, AP
- **Folder:** `/data/patient/2125-11-07_20-20-09_s54437537/`
- **Report:** `/data/patient/2125-11-07_20-20-09_s54437537/report.txt`
- **Images:** `/data/patient/2125-11-07_20-20-09_s54437537/64c99cbe-e1457ba5-58d940df-68b406e8-2a430fdc.jpg`, `/data/patient/2125-11-07_20-20-09_s54437537/6f3ad43a-df5c6fdb-9ca593fc-13d161a4-8869dd8f.jpg`

### Prior Study 39: 54434271
- **Date:** 2125-12-21 13:26:02
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2125-12-21_13-26-02_s54434271/`
- **Report:** `/data/patient/2125-12-21_13-26-02_s54434271/report.txt`
- **Images:** `/data/patient/2125-12-21_13-26-02_s54434271/e8149721-c9e4afbc-7a9dde4a-3c9f7362-fec663a4.jpg`

### Prior Study 40: 56680584
- **Date:** 2125-12-21 17:23:39
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2125-12-21_17-23-39_s56680584/`
- **Report:** `/data/patient/2125-12-21_17-23-39_s56680584/report.txt`
- **Images:** `/data/patient/2125-12-21_17-23-39_s56680584/ef97e724-84de20c9-3e73a8b5-65a01e95-2f82137a.jpg`

### Prior Study 41: 51130329
- **Date:** 2125-12-22 05:06:55
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP, AP
- **Folder:** `/data/patient/2125-12-22_05-06-55_s51130329/`
- **Report:** `/data/patient/2125-12-22_05-06-55_s51130329/report.txt`
- **Images:** `/data/patient/2125-12-22_05-06-55_s51130329/adf296d0-4fd5ce49-a34b75c5-450e6912-f2fba814.jpg`, `/data/patient/2125-12-22_05-06-55_s51130329/b3a59eff-ce2b4a69-c5090087-1a2a391b-2605a57c.jpg`

### Prior Study 42: 52488909
- **Date:** 2125-12-23 04:54:10
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2125-12-23_04-54-10_s52488909/`
- **Report:** `/data/patient/2125-12-23_04-54-10_s52488909/report.txt`
- **Images:** `/data/patient/2125-12-23_04-54-10_s52488909/2501dbf9-714acd96-ca4fba08-e02967b8-23f99f37.jpg`

### Prior Study 43: 59649088
- **Date:** 2126-01-22 16:29:12
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, AP
- **Folder:** `/data/patient/2126-01-22_16-29-12_s59649088/`
- **Report:** `/data/patient/2126-01-22_16-29-12_s59649088/report.txt`
- **Images:** `/data/patient/2126-01-22_16-29-12_s59649088/14782ed9-49fc2401-ac349dd1-0a9b89e0-5425836b.jpg`, `/data/patient/2126-01-22_16-29-12_s59649088/32f9d0a6-a71c3e37-8285ac35-90d110a9-d3f838cf.jpg`

## Target Study

- **Study ID:** 54756918
- **Date:** 2126-01-28 14:04:43
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2126-01-28_14-04-43_s54756918/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2126-01-28_14-04-43_s54756918/641cc7ad-8d3dc0c6-ee97f6e1-7bf62c19-d12ac7bd.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

**HISTORY:** CHF, lethargy and hypotension.  Please assess for pneumonia or
 pulmonary edema.

**TECHNIQUE:** AP upright portable chest radiograph.

**COMPARISON:** ___.

## Your Task

Produce ONLY the FINDINGS and IMPRESSION sections of the target study's report.
Use the target study's images, the provided sections above, and the patient's
prior imaging history (reports + images in `/data/patient/`) as context.

Format your `final_answer` exactly as:

```
FINDINGS:
<your findings text>

IMPRESSION:
<your impression text>
```

Do NOT include EXAMINATION/INDICATION/TECHNIQUE/COMPARISON/HISTORY headers in
your answer — they are already part of the report and will be combined externally.

## Submission Rules

- Set `final_answer` to FINDINGS + IMPRESSION text only (free text)
- Do NOT modify `task_id` or `instruction` fields
- Work autonomously until the submission is complete

**IMPORTANT: update `submission.json` using a JSON-aware tool (e.g., `python -c "import json; ..."`),
NOT by editing the raw text. Manual string edits easily corrupt the JSON.**