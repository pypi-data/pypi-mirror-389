# AWS Cost Calculation Methodology

## Formula Overview

The cost calculator computes a **daily rate** and **annual projection** for AWS spend across multiple accounts using a standardized methodology that matches the AWS Cost Explorer console.

## What's Included

### Operational Costs
- **All AWS services** billed under `BILLING_ENTITY = "AWS"`
- **Metric:** Net Amortized Cost
- **Accounts:** Multiple linked AWS accounts
- **Date Range:** 30-day rolling window, offset by 2 days from calculation date

### Support Costs
- **AWS Support fees** from the 1st of the month containing the end date
- **Allocation:** 50% allocation (÷2)
- **Distribution:** Divided by days in the support month (e.g., 31 for October)

## What's Excluded

1. **Tax** - Excluded via `RECORD_TYPE != "Tax"`
2. **Marketplace Services** - Excluded via `BILLING_ENTITY = "AWS"` filter
   - Third-party SaaS subscriptions
   - Marketplace software licenses
   - Non-AWS vendor services
3. **Support** - Excluded from operational costs, calculated separately

## Calculation Steps

### Step 1: Date Range Calculation
```
Today = Calculation date (e.g., Nov 4, 2025)
Offset = 2 days (default)
Window = 30 days (default)

End Date = Today - Offset = Nov 2, 2025
Start Date = End Date - Window = Oct 3, 2025

Analysis Period: Oct 3 - Nov 2, 2025 (30 days)
```

### Step 2: Operational Cost Calculation
```
Total Operational Cost = Sum of daily Net Amortized Costs
  WHERE:
    - Linked Account IN [configured accounts]
    - Billing Entity = "AWS"
    - Record Type NOT IN ["Tax", "Support"]
    - Date BETWEEN Start Date AND End Date

Days in Support Month = Days in month containing End Date (e.g., 31 for October)

Daily Operational = Total Operational Cost ÷ Days in Support Month
```

**Note:** We divide by the days in the support month (31 for October), NOT the window size (30 days). This matches the AWS console calculation.

### Step 3: Support Cost Calculation
```
Support Date = 1st of month containing End Date (e.g., Nov 1 for Oct 3-Nov 2 period)

Support Cost = Net Amortized Cost on Support Date
  WHERE:
    - Linked Account IN [configured accounts]
    - Record Type = "Support"
    - Date = Support Date

Support Per Day = (Support Cost ÷ 2) ÷ Days in Support Month
```

**Rationale:** Support is charged on the 1st of each month for the previous month's usage. For an October analysis, we use the November 1st support charge (which reflects October usage based on September costs).

### Step 4: Final Calculation
```
Daily Rate = Daily Operational + Support Per Day

Annual Projection = Daily Rate × 365
```

## Example Calculation

**Analysis Period:** Oct 3 - Nov 2, 2025

```
Total Operational Cost:     $450,000.00
Days in October:            31
Daily Operational:          $450,000.00 ÷ 31 = $14,516.13

Support (Nov 1):            $15,000.00
Support Per Day:            ($15,000.00 ÷ 2) ÷ 31 = $241.94

Daily Rate:                 $14,516.13 + $241.94 = $14,758.07
Annual Projection:          $14,758.07 × 365 = $5,386,695
```

## Key Principles

1. **Consistency:** Always use the same filters and methodology
2. **Accuracy:** Match AWS Cost Explorer console calculations exactly
3. **Transparency:** All costs are Net Amortized (includes RI/SP discounts)
4. **Allocation:** Support can be split between entities (default 50/50)
5. **Timeliness:** Use T-2 offset to ensure data completeness

## Validation

To validate the calculation:
1. Open AWS Cost Explorer console
2. Set date range to the analysis period
3. Filter by your linked accounts
4. Set Billing Entity = AWS
5. Exclude Tax and Support
6. Compare total: Should match "Total Operational Cost"
7. Daily average in console ÷ 31 days should match "Daily Operational"

## CLI Usage

```bash
# Default calculation (today - 2 days, 30-day window)
cc calculate --profile myprofile

# Specific start date
cc calculate --profile myprofile --start-date 2025-11-04

# Custom offset and window
cc calculate --profile myprofile --offset 2 --window 30

# JSON output
cc calculate --profile myprofile --json-output
```
