# KB Evidence Exception Summary

Generated UTC: `2026-05-12T13:17:11.013385+00:00`

## Overview

- Documents with exceptions: 4
- Total exceptions: 23
- High-severity exceptions: 10
- Medium-severity exceptions: 6
- Low-severity exceptions: 7

## Interpretation

High-severity exceptions are KB rows that reference a bug / patch number but did not map to an extracted PFDS attachment in the referenced portfolio. These are the primary review candidates.

Medium-severity exceptions are KB rows that cannot be joined automatically because the row does not include a bug / patch identifier or has ambiguous evidence. These need source review before automation can claim coverage.

Low-severity exceptions are cases where the KB or portfolio explicitly indicates that no PFD was provided. These are not missing-evidence failures, but they should remain visible because they affect downstream analysis depth.

## Severity Counts

- High: 10
- Low: 7
- Medium: 6

## Status Counts

- KB explicitly declares no PFD: 6
- Missing extracted PFDS evidence: 10
- Portfolio contains no-PFDS placeholder: 1
- KB row missing bug / patch identifier: 6

## Exceptions by KB

- Kb869018: 8
- Kb875759: 7
- Kb881135: 1
- Kb881136: 7

## High-Severity Exceptions

| KB | MP | Release Date | Bug / Patch | Product | Category | Portfolio | Description |
|---|---|---|---|---|---|---|---|
| KB881136 | MP 1 | April 04, 2026 | 38983801 | Oracle Utilities Customer Care and Billing | Notification Preferences | CCS_26.4_MP1.1.0_PFDs_Portfolio.pdf | Notification-related Issues |
| KB881136 | MP 1 | April 04, 2026 | 39007153 | Oracle Utilities Customer Care and Billing | Customer 360 | CCS_26.4_MP1.1.0_PFDs_Portfolio.pdf | Additional changes to display AI-generated summary to Customer Activity History zone |
| KB881135 | MP 7 | April 04, 2026 | 38932135 | Oracle Utilities Customer to Meter | Market Transaction Messaging | CCS_25.10_MP7.1.0_PFDs_Portfolio.pdf | Database Health Check: Orphan Records - MTM objects and system generated imports on scripts |
| KB869018 | MP 5 | February 07, 2026 | 38889566 | Oracle Utilities Customer to Meter | Market Transaction Messaging | CCS_25.10_MP5.1.0_PFDs_Portfolio.pdf | Custom Modification algorithm types cleanup |
| KB869018 | MP 5 | February 07, 2026 | 38866025 | Oracle Utilities Customer to Meter | Market Transaction Messaging | CCS_25.10_MP5.1.0_PFDs_Portfolio.pdf | Incorrect value if Market Participant Type is set to 'AY' |
| KB869018 | MP 5 | February 07, 2026 | 38765800 | Oracle Utilities Customer to Meter | Market Transaction Messaging | CCS_25.10_MP5.1.0_PFDs_Portfolio.pdf | Market Transaction Messages 867_03/810 non-final not RFP for service point with meter removed, 810s are stuck in 'Investigate' / 'Cancel' status |
| KB869018 | MP 5 | February 07, 2026 | 38711109 | Oracle Utilities Customer to Meter | Market Transaction Messaging | CCS_25.10_MP5.1.0_PFDs_Portfolio.pdf | U2BILLGENPRC algorithm needs to be fixed to ignore adjustment only bill |
| KB869018 | MP 5 | February 07, 2026 | 38803958 | Oracle Utilities Customer to Meter | Market Transaction Messaging | CCS_25.10_MP5.1.0_PFDs_Portfolio.pdf | Error upon viewing a service agreement - field name 'ACT_ERROR_MESSAGE' that does not exist |
| KB869018 | MP 5 | February 07, 2026 | 38803048 | Oracle Utilities Customer to Meter | Market Transaction Messaging | CCS_25.10_MP5.1.0_PFDs_Portfolio.pdf | Various MTM transaction and zone errors |
| KB869018 | MP 5 | February 07, 2026 | 38719400 | Oracle Utilities Customer to Meter | Market Transaction Messaging | CCS_25.10_MP5.1.0_PFDs_Portfolio.pdf | Remove 'Error Status' soft parameter from U2VALMM algorithm |

## Document Breakdown

### KB881136 — MP 1

Source: `kbs/raw/April 2026 Maintenance Pack - MP 1.html`

Exception count: 7

- KB explicitly declares no PFD: 1
- Missing extracted PFDS evidence: 2
- Portfolio contains no-PFDS placeholder: 1
- KB row missing bug / patch identifier: 3

### KB881135 — MP 7

Source: `kbs/raw/April 2026 Maintenance Pack - MP 7.html`

Exception count: 1

- Missing extracted PFDS evidence: 1

### KB869018 — MP 5

Source: `kbs/raw/February 2026 Maintenance Pack - MP 5 - Starting after MP 5.3.1.html`

Exception count: 8

- Missing extracted PFDS evidence: 7
- KB row missing bug / patch identifier: 1

### KB875759 — MP 6

Source: `kbs/raw/March 2026 Maintenance Pack - MP 6.html`

Exception count: 7

- KB explicitly declares no PFD: 5
- KB row missing bug / patch identifier: 2
