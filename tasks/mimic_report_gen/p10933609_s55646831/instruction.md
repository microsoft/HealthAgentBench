# Radiology Report — Findings & Impression Generation

You are working inside a task environment that contains:

- Chest X-ray images for patient `10933609`
- 40 prior study/studies with full reports and images under `/data/patient/`
- Target study images (study `55646831`) — you must generate FINDINGS and IMPRESSION for this study
- Task data at `/workspace/benchmark_tasks.json`
- Editable submission at `/workspace/submission.json`

The other sections of the target report (EXAMINATION, INDICATION, TECHNIQUE,
COMPARISON, HISTORY) are **provided** to you in `benchmark_tasks.json` under
`target_study.given_sections` and in the instruction text. You must NOT regenerate them.

Your final work product is `/workspace/submission.json`.

## Patient History

### Prior Study 1: 59255047
- **Date:** 2151-02-10 10:49:58
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** 
- **Folder:** `/data/patient/2151-02-10_10-49-58_s59255047/`
- **Report:** `/data/patient/2151-02-10_10-49-58_s59255047/report.txt`
- **Images:** `/data/patient/2151-02-10_10-49-58_s59255047/f7593494-5c5778f8-1083d675-46c20f13-3abd5cb2.jpg`

### Prior Study 2: 51401250
- **Date:** 2151-02-16 19:36:31
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** 
- **Folder:** `/data/patient/2151-02-16_19-36-31_s51401250/`
- **Report:** `/data/patient/2151-02-16_19-36-31_s51401250/report.txt`
- **Images:** `/data/patient/2151-02-16_19-36-31_s51401250/ba43f637-2b72b2f5-ad1e7041-96ea8d84-32e18e7e.jpg`

### Prior Study 3: 57053258
- **Date:** 2151-03-02 18:55:07
- **Procedure:** Performed Desc
- **Views:** PA, LL, PA
- **Folder:** `/data/patient/2151-03-02_18-55-07_s57053258/`
- **Report:** `/data/patient/2151-03-02_18-55-07_s57053258/report.txt`
- **Images:** `/data/patient/2151-03-02_18-55-07_s57053258/2a78a082-bf1c63ea-400d5e85-edf9eacf-5ede056d.jpg`, `/data/patient/2151-03-02_18-55-07_s57053258/7699bdde-b4b344e6-8109dc76-dd9e5dc5-2f06b11a.jpg`, `/data/patient/2151-03-02_18-55-07_s57053258/7f53537b-fa6d85dc-ba21f7bb-f4c04a3c-177aeed6.jpg`

### Prior Study 4: 52866895
- **Date:** 2151-03-06 21:23:24
- **Procedure:** Performed Desc
- **Views:** PA, LL
- **Folder:** `/data/patient/2151-03-06_21-23-24_s52866895/`
- **Report:** `/data/patient/2151-03-06_21-23-24_s52866895/report.txt`
- **Images:** `/data/patient/2151-03-06_21-23-24_s52866895/2584ab7b-dd93b49c-2783f1d8-ee64a307-80ff57b5.jpg`, `/data/patient/2151-03-06_21-23-24_s52866895/d9e98604-eb7e8cc5-30faf2ad-8c5f7035-f7e13a76.jpg`

### Prior Study 5: 56058164
- **Date:** 2151-03-21 13:39:12
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, AP
- **Folder:** `/data/patient/2151-03-21_13-39-12_s56058164/`
- **Report:** `/data/patient/2151-03-21_13-39-12_s56058164/report.txt`
- **Images:** `/data/patient/2151-03-21_13-39-12_s56058164/16fbacce-c16d2bb4-ab113b1b-2956fc48-9f78a96d.jpg`, `/data/patient/2151-03-21_13-39-12_s56058164/67106e2c-168fd4e2-52fbcc7d-4c4b2f27-5499c157.jpg`

### Prior Study 6: 52402828
- **Date:** 2151-03-26 17:33:31
- **Procedure:** CHEST (PA AND LAT)
- **Views:** PA, LATERAL, PA
- **Folder:** `/data/patient/2151-03-26_17-33-31_s52402828/`
- **Report:** `/data/patient/2151-03-26_17-33-31_s52402828/report.txt`
- **Images:** `/data/patient/2151-03-26_17-33-31_s52402828/318975e1-0f1046f7-331e3d92-185e4805-d5ac3b65.jpg`, `/data/patient/2151-03-26_17-33-31_s52402828/c0023bba-56efba28-c654ac42-24227b01-0157a8c2.jpg`, `/data/patient/2151-03-26_17-33-31_s52402828/e19a6258-3792982e-db47dccd-c9961bb6-e0aeba69.jpg`

### Prior Study 7: 55438657
- **Date:** 2151-05-10 12:26:52
- **Procedure:** 
- **Views:** PA, LL
- **Folder:** `/data/patient/2151-05-10_12-26-52_s55438657/`
- **Report:** `/data/patient/2151-05-10_12-26-52_s55438657/report.txt`
- **Images:** `/data/patient/2151-05-10_12-26-52_s55438657/4a706f94-eae311b0-de845977-dcc52bde-4615615e.jpg`, `/data/patient/2151-05-10_12-26-52_s55438657/75869cde-a41c0128-bd418fb5-b3e4f46b-8f003c99.jpg`

### Prior Study 8: 55447530
- **Date:** 2151-05-14 17:36:43
- **Procedure:** 
- **Views:** LL, PA, PA
- **Folder:** `/data/patient/2151-05-14_17-36-43_s55447530/`
- **Report:** `/data/patient/2151-05-14_17-36-43_s55447530/report.txt`
- **Images:** `/data/patient/2151-05-14_17-36-43_s55447530/3128f453-ad0dbc35-9cce331f-ca0db591-52e9cbab.jpg`, `/data/patient/2151-05-14_17-36-43_s55447530/67046a75-310cfff1-2dd57e2f-6208c141-d18736f5.jpg`, `/data/patient/2151-05-14_17-36-43_s55447530/92fe0d65-6cd5e4b6-22dbcaec-949cb8bd-1c28d956.jpg`

### Prior Study 9: 50289849
- **Date:** 2151-05-26 17:40:23
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, PA, PA
- **Folder:** `/data/patient/2151-05-26_17-40-23_s50289849/`
- **Report:** `/data/patient/2151-05-26_17-40-23_s50289849/report.txt`
- **Images:** `/data/patient/2151-05-26_17-40-23_s50289849/57c03361-059aa6a2-9f7028da-423292f4-3b134303.jpg`, `/data/patient/2151-05-26_17-40-23_s50289849/add88ac4-2338dc16-a58a1ae9-57b1ecae-0a8f018a.jpg`, `/data/patient/2151-05-26_17-40-23_s50289849/ed54d9af-c03fa3e8-2c18f99d-c0c65bc5-98bf2656.jpg`

### Prior Study 10: 54853227
- **Date:** 2151-07-04 19:09:04
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2151-07-04_19-09-04_s54853227/`
- **Report:** `/data/patient/2151-07-04_19-09-04_s54853227/report.txt`
- **Images:** `/data/patient/2151-07-04_19-09-04_s54853227/c3994ff3-e8774cd2-b7a4c40c-959819fa-d8d942b6.jpg`

### Prior Study 11: 52247073
- **Date:** 2151-07-05 14:57:28
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2151-07-05_14-57-28_s52247073/`
- **Report:** `/data/patient/2151-07-05_14-57-28_s52247073/report.txt`
- **Images:** `/data/patient/2151-07-05_14-57-28_s52247073/3391a4a6-64cc1ac6-443cb01a-5a13d4c2-c6b2a84d.jpg`

### Prior Study 12: 59018975
- **Date:** 2151-07-06 04:55:49
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2151-07-06_04-55-49_s59018975/`
- **Report:** `/data/patient/2151-07-06_04-55-49_s59018975/report.txt`
- **Images:** `/data/patient/2151-07-06_04-55-49_s59018975/ca5edfd1-791faa24-0e6c7747-b17088d0-d90a8fc2.jpg`

### Prior Study 13: 59885828
- **Date:** 2151-07-09 19:37:40
- **Procedure:** Performed Desc
- **Views:** LL, PA
- **Folder:** `/data/patient/2151-07-09_19-37-40_s59885828/`
- **Report:** `/data/patient/2151-07-09_19-37-40_s59885828/report.txt`
- **Images:** `/data/patient/2151-07-09_19-37-40_s59885828/ec78e0b4-c858f616-11d4e328-ff8d6f90-4a6acef0.jpg`, `/data/patient/2151-07-09_19-37-40_s59885828/f52047f3-b0ba5171-755f7044-afcf59b8-62848096.jpg`

### Prior Study 14: 57629869
- **Date:** 2151-08-05 14:24:29
- **Procedure:** CHEST (PA AND LAT)
- **Views:** AP, AP
- **Folder:** `/data/patient/2151-08-05_14-24-29_s57629869/`
- **Report:** `/data/patient/2151-08-05_14-24-29_s57629869/report.txt`
- **Images:** `/data/patient/2151-08-05_14-24-29_s57629869/68fe8811-11486a87-1a63faec-cbde0858-b889b677.jpg`, `/data/patient/2151-08-05_14-24-29_s57629869/93894f42-2000f601-7b1944a8-7c4c0711-3d3a2a9b.jpg`

### Prior Study 15: 59225625
- **Date:** 2151-08-21 20:20:05
- **Procedure:** CHEST (PA AND LAT)
- **Views:** PA, LATERAL, PA
- **Folder:** `/data/patient/2151-08-21_20-20-05_s59225625/`
- **Report:** `/data/patient/2151-08-21_20-20-05_s59225625/report.txt`
- **Images:** `/data/patient/2151-08-21_20-20-05_s59225625/7491ba73-b81aa431-0b41a7cb-733d87f1-4523ba29.jpg`, `/data/patient/2151-08-21_20-20-05_s59225625/f67b2368-01c7950b-b586b58b-6d8c66a4-c8b17db2.jpg`, `/data/patient/2151-08-21_20-20-05_s59225625/f79eadd6-c024fbbc-dec2a8a7-0d75c594-a53f0aa1.jpg`

### Prior Study 16: 58929044
- **Date:** 2151-09-07 15:27:56
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, PA, PA
- **Folder:** `/data/patient/2151-09-07_15-27-56_s58929044/`
- **Report:** `/data/patient/2151-09-07_15-27-56_s58929044/report.txt`
- **Images:** `/data/patient/2151-09-07_15-27-56_s58929044/282d803b-7e9e211b-ccf6ccf5-f3885dec-b8b9f76b.jpg`, `/data/patient/2151-09-07_15-27-56_s58929044/a603cd8b-deb5791e-0af13e1c-291d022f-105c7d5c.jpg`, `/data/patient/2151-09-07_15-27-56_s58929044/dda9463c-13653db6-03e65f74-74ef0b98-4cceb8c9.jpg`

### Prior Study 17: 56535476
- **Date:** 2151-09-24 17:43:20
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, AP
- **Folder:** `/data/patient/2151-09-24_17-43-20_s56535476/`
- **Report:** `/data/patient/2151-09-24_17-43-20_s56535476/report.txt`
- **Images:** `/data/patient/2151-09-24_17-43-20_s56535476/5740ef70-f0368542-f6ff1baf-09a39fdc-33e82710.jpg`, `/data/patient/2151-09-24_17-43-20_s56535476/fa80d52e-25c85b24-0302d3d0-f2052c45-6faebca9.jpg`

### Prior Study 18: 56267214
- **Date:** 2151-09-26 15:44:19
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP, AP
- **Folder:** `/data/patient/2151-09-26_15-44-19_s56267214/`
- **Report:** `/data/patient/2151-09-26_15-44-19_s56267214/report.txt`
- **Images:** `/data/patient/2151-09-26_15-44-19_s56267214/157aae90-df977bc0-da3b3a41-87cc0fcb-438b3e17.jpg`, `/data/patient/2151-09-26_15-44-19_s56267214/dc460b17-20bafc45-b91e6c92-311eb0ad-7ea1a883.jpg`

### Prior Study 19: 56304327
- **Date:** 2151-09-28 14:17:00
- **Procedure:** Performed Desc
- **Views:** LL, PA
- **Folder:** `/data/patient/2151-09-28_14-17-00_s56304327/`
- **Report:** `/data/patient/2151-09-28_14-17-00_s56304327/report.txt`
- **Images:** `/data/patient/2151-09-28_14-17-00_s56304327/1844f765-ae8c22e1-b7f8d30e-03b721fb-83a616a9.jpg`, `/data/patient/2151-09-28_14-17-00_s56304327/b9c18cbb-323135fb-0118b586-6d8846f0-a1099863.jpg`

### Prior Study 20: 50380704
- **Date:** 2151-12-10 17:53:14
- **Procedure:** CHEST (PA AND LAT)
- **Views:** PA, PA, LATERAL
- **Folder:** `/data/patient/2151-12-10_17-53-14_s50380704/`
- **Report:** `/data/patient/2151-12-10_17-53-14_s50380704/report.txt`
- **Images:** `/data/patient/2151-12-10_17-53-14_s50380704/0f7b9130-cdf81a79-d3e0a0cc-4e06df3c-dfc97cab.jpg`, `/data/patient/2151-12-10_17-53-14_s50380704/2b34055b-5ae8bcf1-5a188ee8-135d064b-19c2f6ce.jpg`, `/data/patient/2151-12-10_17-53-14_s50380704/ccc0c158-17216b52-657aee65-021bde6c-6932d2a9.jpg`

### Prior Study 21: 54870311
- **Date:** 2151-12-20 20:42:03
- **Procedure:** CHEST (PA AND LAT)
- **Views:** PA, LATERAL
- **Folder:** `/data/patient/2151-12-20_20-42-03_s54870311/`
- **Report:** `/data/patient/2151-12-20_20-42-03_s54870311/report.txt`
- **Images:** `/data/patient/2151-12-20_20-42-03_s54870311/7acf30bd-0ed39a38-bb6159dd-2ed09689-dd05ba98.jpg`, `/data/patient/2151-12-20_20-42-03_s54870311/95527da6-78fdab9e-2d3b3782-9aa97e06-a3e69c13.jpg`

### Prior Study 22: 51002383
- **Date:** 2152-02-15 15:35:50
- **Procedure:** CHEST (PA AND LAT)
- **Views:** PA, LATERAL
- **Folder:** `/data/patient/2152-02-15_15-35-50_s51002383/`
- **Report:** `/data/patient/2152-02-15_15-35-50_s51002383/report.txt`
- **Images:** `/data/patient/2152-02-15_15-35-50_s51002383/5668d9ef-e5b61aae-8a38e823-b668e8ba-837392e7.jpg`, `/data/patient/2152-02-15_15-35-50_s51002383/c9cd6c49-2bebaea2-82c0c5dc-c3d2e9a7-560599b0.jpg`

### Prior Study 23: 54300688
- **Date:** 2152-05-17 22:12:09
- **Procedure:** CHEST (PA AND LAT)
- **Views:** PA, LATERAL
- **Folder:** `/data/patient/2152-05-17_22-12-09_s54300688/`
- **Report:** `/data/patient/2152-05-17_22-12-09_s54300688/report.txt`
- **Images:** `/data/patient/2152-05-17_22-12-09_s54300688/21f6f51a-c6b2fab8-8c228bb8-1a8f8c46-d568b413.jpg`, `/data/patient/2152-05-17_22-12-09_s54300688/962a470a-df0275b5-6b8e2125-e3cc9c90-bf7e0a66.jpg`

### Prior Study 24: 54422699
- **Date:** 2152-05-31 05:09:51
- **Procedure:** CHEST (PA AND LAT)
- **Views:** AP, LATERAL
- **Folder:** `/data/patient/2152-05-31_05-09-51_s54422699/`
- **Report:** `/data/patient/2152-05-31_05-09-51_s54422699/report.txt`
- **Images:** `/data/patient/2152-05-31_05-09-51_s54422699/53c18304-54fac49c-cabe4615-c2a37b60-8555c705.jpg`, `/data/patient/2152-05-31_05-09-51_s54422699/72a3f5c1-9ff27189-d2d045aa-ee3f3b3b-8d4f144f.jpg`

### Prior Study 25: 54694185
- **Date:** 2152-06-13 23:04:55
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, PA
- **Folder:** `/data/patient/2152-06-13_23-04-55_s54694185/`
- **Report:** `/data/patient/2152-06-13_23-04-55_s54694185/report.txt`
- **Images:** `/data/patient/2152-06-13_23-04-55_s54694185/4778cb0a-f3b1679a-db7c043c-cfdd71ef-5b2da652.jpg`, `/data/patient/2152-06-13_23-04-55_s54694185/ff86990a-2b9b1ae4-abec4188-55d0170a-72142dca.jpg`

### Prior Study 26: 50636786
- **Date:** 2152-06-30 17:29:06
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2152-06-30_17-29-06_s50636786/`
- **Report:** `/data/patient/2152-06-30_17-29-06_s50636786/report.txt`
- **Images:** `/data/patient/2152-06-30_17-29-06_s50636786/8452bd2c-ba775d23-e46872fa-f0e9c5bd-63897743.jpg`

### Prior Study 27: 50290463
- **Date:** 2152-07-07 06:23:58
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, AP
- **Folder:** `/data/patient/2152-07-07_06-23-58_s50290463/`
- **Report:** `/data/patient/2152-07-07_06-23-58_s50290463/report.txt`
- **Images:** `/data/patient/2152-07-07_06-23-58_s50290463/000ffbff-3d93bcef-da8b17cd-fbcede53-51728df9.jpg`, `/data/patient/2152-07-07_06-23-58_s50290463/f576c221-e516f6b2-ee125faa-a1af8c31-ed2991b8.jpg`

### Prior Study 28: 52935265
- **Date:** 2152-07-22 19:54:00
- **Procedure:** CHEST (PA AND LAT)
- **Views:** PA, LATERAL
- **Folder:** `/data/patient/2152-07-22_19-54-00_s52935265/`
- **Report:** `/data/patient/2152-07-22_19-54-00_s52935265/report.txt`
- **Images:** `/data/patient/2152-07-22_19-54-00_s52935265/9587ec7a-e6b7082f-0b22b670-b924b608-674375e2.jpg`, `/data/patient/2152-07-22_19-54-00_s52935265/fa29a6c8-729bdd50-764451b7-b92da9bc-daf265ee.jpg`

### Prior Study 29: 57695180
- **Date:** 2152-07-28 15:58:46
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2152-07-28_15-58-46_s57695180/`
- **Report:** `/data/patient/2152-07-28_15-58-46_s57695180/report.txt`
- **Images:** `/data/patient/2152-07-28_15-58-46_s57695180/c11514bb-319a3161-c0c85326-68094c62-0220f4f4.jpg`

### Prior Study 30: 51115198
- **Date:** 2152-08-02 18:02:50
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2152-08-02_18-02-50_s51115198/`
- **Report:** `/data/patient/2152-08-02_18-02-50_s51115198/report.txt`
- **Images:** `/data/patient/2152-08-02_18-02-50_s51115198/16cf598d-2b1a30e2-627a4c64-25720237-cab9c186.jpg`

### Prior Study 31: 55794889
- **Date:** 2152-08-05 18:01:58
- **Procedure:** 
- **Views:** AP
- **Folder:** `/data/patient/2152-08-05_18-01-58_s55794889/`
- **Report:** `/data/patient/2152-08-05_18-01-58_s55794889/report.txt`
- **Images:** `/data/patient/2152-08-05_18-01-58_s55794889/f0bb1f2a-8ac4c2cb-b85dec90-1fc00f8e-931106fe.jpg`

### Prior Study 32: 50205123
- **Date:** 2152-08-29 18:34:37
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2152-08-29_18-34-37_s50205123/`
- **Report:** `/data/patient/2152-08-29_18-34-37_s50205123/report.txt`
- **Images:** `/data/patient/2152-08-29_18-34-37_s50205123/5df8c586-2f6adf15-722e6f13-ffa8a117-acd92b9a.jpg`

### Prior Study 33: 51816597
- **Date:** 2152-08-29 22:23:16
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2152-08-29_22-23-16_s51816597/`
- **Report:** `/data/patient/2152-08-29_22-23-16_s51816597/report.txt`
- **Images:** `/data/patient/2152-08-29_22-23-16_s51816597/b6958192-e9ba61f7-b0d3e5ab-5562c733-a0ad2714.jpg`

### Prior Study 34: 57290683
- **Date:** 2152-09-05 15:21:45
- **Procedure:** CHEST (PA AND LAT)
- **Views:** AP, LATERAL
- **Folder:** `/data/patient/2152-09-05_15-21-45_s57290683/`
- **Report:** `/data/patient/2152-09-05_15-21-45_s57290683/report.txt`
- **Images:** `/data/patient/2152-09-05_15-21-45_s57290683/9d8483b4-460ba2c2-3a8322ea-4d7df3ca-e1789d06.jpg`, `/data/patient/2152-09-05_15-21-45_s57290683/ba684a87-3ecff165-b646c20d-ce6363d4-5a11761e.jpg`

### Prior Study 35: 51826402
- **Date:** 2152-10-11 12:21:41
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2152-10-11_12-21-41_s51826402/`
- **Report:** `/data/patient/2152-10-11_12-21-41_s51826402/report.txt`
- **Images:** `/data/patient/2152-10-11_12-21-41_s51826402/1ccba7cb-19cab96d-3af214af-04c55ded-7842012a.jpg`

### Prior Study 36: 53512860
- **Date:** 2152-10-18 10:46:01
- **Procedure:** CHEST (PORTABLE AP)
- **Views:** AP
- **Folder:** `/data/patient/2152-10-18_10-46-01_s53512860/`
- **Report:** `/data/patient/2152-10-18_10-46-01_s53512860/report.txt`
- **Images:** `/data/patient/2152-10-18_10-46-01_s53512860/3e25d193-509147d7-b305908a-51e0da17-7cb23fda.jpg`

### Prior Study 37: 55736427
- **Date:** 2152-10-25 21:52:15
- **Procedure:** CHEST (PA AND LAT)
- **Views:** PA, LATERAL
- **Folder:** `/data/patient/2152-10-25_21-52-15_s55736427/`
- **Report:** `/data/patient/2152-10-25_21-52-15_s55736427/report.txt`
- **Images:** `/data/patient/2152-10-25_21-52-15_s55736427/1a734389-4bcb9234-220a253e-c22386fd-4f018ada.jpg`, `/data/patient/2152-10-25_21-52-15_s55736427/4b842f9a-e380a620-f62f355a-f706be25-95150ec3.jpg`

### Prior Study 38: 59243134
- **Date:** 2153-02-16 03:57:50
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, AP, LATERAL
- **Folder:** `/data/patient/2153-02-16_03-57-50_s59243134/`
- **Report:** `/data/patient/2153-02-16_03-57-50_s59243134/report.txt`
- **Images:** `/data/patient/2153-02-16_03-57-50_s59243134/56d68575-e620ef2b-9e25dbcd-faa3f9d8-2f61e0ca.jpg`, `/data/patient/2153-02-16_03-57-50_s59243134/bb067a71-304abf94-bb1611d4-e8ac9115-189005f3.jpg`, `/data/patient/2153-02-16_03-57-50_s59243134/c5cb6fb9-7d707bd6-72335a6c-80038c03-35e3eb27.jpg`

### Prior Study 39: 54537700
- **Date:** 2153-02-20 11:10:01
- **Procedure:** Performed Desc
- **Views:** LL, PA
- **Folder:** `/data/patient/2153-02-20_11-10-01_s54537700/`
- **Report:** `/data/patient/2153-02-20_11-10-01_s54537700/report.txt`
- **Images:** `/data/patient/2153-02-20_11-10-01_s54537700/396061be-a852cd47-7e3c4e82-3b2ec2b9-4e9632ff.jpg`, `/data/patient/2153-02-20_11-10-01_s54537700/406539e1-fd9fe3f2-6192f2a5-e24d2d07-5ff88d1d.jpg`

### Prior Study 40: 52624179
- **Date:** 2153-05-01 04:29:41
- **Procedure:** CHEST (PA AND LAT)
- **Views:** LATERAL, AP
- **Folder:** `/data/patient/2153-05-01_04-29-41_s52624179/`
- **Report:** `/data/patient/2153-05-01_04-29-41_s52624179/report.txt`
- **Images:** `/data/patient/2153-05-01_04-29-41_s52624179/225164ad-9f7e5e4f-b9c9e387-2b07cdd5-10488e8b.jpg`, `/data/patient/2153-05-01_04-29-41_s52624179/c89c7ca8-466643b7-e8480932-1b791a6f-4ae17f31.jpg`

## Target Study

- **Study ID:** 55646831
- **Date:** 2153-08-11 15:09:58
- **Procedure:** CHEST (PA AND LAT)
- **Views:** PA, PA, LATERAL
- **Folder:** `/data/patient/2153-08-11_15-09-58_s55646831/` (contains only `.jpg` images — no `report.txt`)
- **Images:** `/data/patient/2153-08-11_15-09-58_s55646831/1e31fec1-1f4cbc01-4583b395-5127c6f7-43b9a7e7.jpg`, `/data/patient/2153-08-11_15-09-58_s55646831/e26fdf14-791d85bf-3beaee42-3ec8bcee-4a05efee.jpg`, `/data/patient/2153-08-11_15-09-58_s55646831/f8b70248-0a9f8ab0-ea3de70b-7d93e712-416c0c78.jpg`

### Provided sections of the target report

These are GIVEN to you. Use them as context but do NOT include them in your output.

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