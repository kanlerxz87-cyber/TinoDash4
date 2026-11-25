/*
 * Source register, glossary, timeline, flagged items, suggestions, and copy.
 * Every table row on the site must cite an entry here. Unverified items are listed in FLAGGED.
 * Privacy: no addresses, names, APNs, ZIP codes, assessed values, or SF rent figures are written here.
 */
'use strict';

const SOURCES = {
  revproc: { title: 'IRS Rev. Proc. 2025-32 (2026 inflation adjustments, basic exclusion, capital-gain thresholds)', url: 'https://www.irs.gov/pub/irs-drop/rp-25-32.pdf', status: 'verified' },
  irsEstate: { title: 'IRS: Estate Tax (2026 filing threshold $15,000,000)', url: 'https://www.irs.gov/businesses/small-businesses-self-employed/estate-tax', status: 'verified' },
  i706: { title: 'IRS Form 706 instructions (07/2026 edition)', url: 'https://www.irs.gov/instructions/i706', status: 'partly read (structure only); 9-month deadline NOT found' },
  pub551: { title: 'IRS Publication 551, Basis of Assets (12/2025)', url: 'https://www.irs.gov/publications/p551', status: 'verified (chunks 4, 6, 8, 9, 11); IRC §1014 text not read' },
  boeProp19: { title: 'BOE: Prop 19 comparison tables (RTC §63.2 and §69.6)', url: 'https://www.boe.ca.gov/prop19/', status: 'verified' },
  lta25009: { title: 'BOE Letter to Assessors 2025/009: indexed amount $1,044,586', url: 'https://www.boe.ca.gov/proptaxes/pdf/lta25009.pdf', status: 'verified' },
  lta26002: { title: 'BOE Letter to Assessors 2026/002: 2026-27 inflation factor 1.02', url: 'https://www.boe.ca.gov/proptaxes/pdf/lta26002.pdf', status: 'verified' },
  lta26026: { title: 'BOE Letter to Assessors 2026/026: Prop 19 FAQ (chunks 0-2 read)', url: 'https://www.boe.ca.gov/proptaxes/pdf/lta26026.pdf', status: 'partly verified (chunks 3-10 unread)' },
  ftb540: { title: 'FTB 2025 Form 540 booklet (due dates, 12.30% top rate, Schedule X/Y/Z)', url: 'https://www.ftb.ca.gov/forms/2025/2025-540-booklet.html', status: 'verified (chunks 21, 24)' },
  rtc17043: { title: 'California Revenue & Taxation Code §17043 (1% surcharge over $1,000,000)', url: 'https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=RTC&sectionNum=17043', status: 'verified' },
  rtc11911: { title: 'California Revenue & Taxation Code §11911 (county documentary transfer tax)', url: 'https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=RTC&sectionNum=11911', status: 'verified' },
  prob13100: { title: 'California Probate Code §13100 (small-estate affidavit, 40 days)', url: 'https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=PROB&sectionNum=13100', status: 'verified' },
  ssa2026: { title: 'SSA 2026 Trustees Report: long-range CPI-W assumptions (Alt I, II, III)', url: 'https://www.ssa.gov/oact/tr/2026/index.html', status: 'verified (summary); see long-range assumptions PDF' },
  ssaLRA: { title: 'SSA 2026 Long-Range Economic Assumptions', url: 'https://www.ssa.gov/oact/tr/2026/2026_Long-Range_Economic_Assumptions.pdf', status: 'verified' },
  fed1929: { title: 'Federal Reserve History: Stock Market Crash of 1929', url: 'https://www.federalreservehistory.org/essays/stock-market-crash-of-1929', status: 'verified (Dow -89%, 1929-32; regained Nov 1954)' },
  blsCpi: { title: 'BLS CPI news release (CPI-U Oct 2026 index 337.511; 12-month change not published)', url: 'https://www.bls.gov/news.release/cpi.nr0.htm', status: 'verified (index); 12-month rate not published' },
  sfRent: { title: 'SF Rent Board: allowable annual increase 2026-27 (1.6%) and 2027-28 (2.3%)', url: 'https://www.sf.gov/news--annual-rent-increase-3127-22928-announced', status: 'verified' },
  sfPUC: { title: 'SFPUC Rate Fairness Board presentation (Mar 19, 2026): FY26-FY28 water and sewer', url: 'https://www.sfpuc.gov/sites/default/files/agendas-minutes-rate-fairness-board/6a-Rates-Presentation.pdf', status: 'verified (summary); line items not verified' },
  sfElec: { title: 'SF Department of Elections: Nov 3, 2026 results (Prop H preliminary)', url: 'https://www.sfelections.org/results/20261103/index.html', status: 'verified (preliminary; certification pending)' },
  sfVIP: { title: 'SF Voter Information Pamphlet, Nov 3, 2026 (Prop H official terms)', url: 'https://media.api.sf.gov/documents/N26_EN_VIP.pdf', status: 'verified (terms); legal text: growsf.org (secondary)' },
  sfTT: { title: 'SF transfer tax rate schedule (sf.gov)', url: 'https://www.sf.gov/information--real-property-transfer-tax', status: 'NOT FETCHED (fetch failed); rates unverified' },
  cdiIns: { title: 'California Department of Insurance: homeowners premium data (2025 data call)', url: 'https://www.insurance.ca.gov/', status: 'secondary only; not fetched directly; flagged' },
  scTax: { title: 'Santa Clara County Controller: property tax rates by tax rate area', url: 'https://www.sccgov.org/', status: 'NOT FETCHED; rates unverified' },
  irc1411: { title: 'IRC §1411 (net investment income tax)', url: 'https://www.law.cornell.edu/uscode/text/26/1411', status: 'NOT FETCHED; rate unverified' },
  irc121: { title: 'IRC §121 (exclusion of gain on principal residence)', url: 'https://www.law.cornell.edu/uscode/text/26/121', status: 'NOT FETCHED; $250,000 amount unverified' },
  irc1014: { title: 'IRC §1014 (basis of property acquired from a decedent)', url: 'https://www.law.cornell.edu/uscode/text/26/1014', status: 'NOT FETCHED (uscode fetch failed); Pub. 551 used instead' },
  irc1031: { title: 'IRC §1031 (like-kind exchanges)', url: 'https://www.law.cornell.edu/uscode/text/26/1031', status: 'NOT FETCHED; CPA to confirm' },
  treasury: { title: 'US Treasury daily par yield curve rates', url: 'https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve', status: 'NOT FETCHED; cash rate flagged' },
};

// Flagged items: anything used in the model or the site that is not verified.
const FLAGGED = [
  { id: 'F01', item: 'Form 706 filing deadline (9 months after death)', why: 'Only secondary sources state it. Not found in the Form 706 instructions chunks read.', need: 'Read further chunks of i706 or IRC §6075(a).', src: 'i706' },
  { id: 'F02', item: 'Form 540 surcharge line placement', why: 'RTC §17043 verified; the line on the 2025 Form 540 was not located.', need: 'Read Form 540 Schedule X/Y/Z and line instructions.', src: 'ftb540' },
  { id: 'F03', item: 'Basic exclusion for prior taxable gifts and portability election', why: 'Secondary sources only. Late portability election window (5 years) is from Rev. Proc. 2022-32, not fetched.', need: 'Fetch Rev. Proc. 2022-32 and the Form 706 portability section.', src: 'revproc' },
  { id: 'F04', item: 'Unified credit, annual gift exclusion ($19,000), and noncitizen-spouse exclusion', why: 'Secondary sources only.', need: 'Verify against Rev. Proc. 2025-32 or IRS annual gift-tax page.', src: 'revproc' },
  { id: 'F05', item: '2026 standard deduction and 2026 income-tax brackets (other than LTCG thresholds)', why: 'Rev. Proc. 2025-32 §4 not read.', need: 'Read Rev. Proc. 2025-32 §4.', src: 'revproc' },
  { id: 'F06', item: 'IRC §1014 statute text (basis at date of death)', why: 'uscode.house.gov fetch failed. Pub. 551 used instead.', need: 'Fetch statute text from a government source.', src: 'irc1014' },
  { id: 'F07', item: 'BOE LTA 2026/026 chunks 3-10 (Prop 19 details, step-transaction, filing mechanics)', why: 'Only chunks 0-2 read.', need: 'Read remaining chunks; confirm one-year occupancy and three-year claim rules.', src: 'lta26026' },
  { id: 'F08', item: 'Prop 19 base-year (factored) value for Property A', why: 'Not supplied in this workspace. Model uses full reassessment at FMV as the conservative fallback.', need: 'Enter the verified base-year value from the County Assessor or tax bill (kept out of publication).', src: 'boeProp19' },
  { id: 'F09', item: 'Santa Clara effective property-tax rate (1.19% secondary)', why: 'County Controller not fetched.', need: 'Confirm rate for the tax rate area of Property A.', src: 'scTax' },
  { id: 'F10', item: 'Homeowner insurance for Property A (ZIP withheld)', why: 'User did not know. Secondary CDI averages only.', need: 'Obtain written quote for a primary residence and a landlord policy.', src: 'cdiIns' },
  { id: 'F11', item: 'Rental comparables for Property A (rule 4)', why: 'None verified. Market yield of 2.5% is an assumption.', need: 'Three verified comparables from a listing or appraisal source.', src: 'fed1929' },
  { id: 'F12', item: 'Selling costs (5%), maintenance reserve (0.75%), and management overhead (8%)', why: 'Assumptions, not sourced.', need: 'Replace with quotes from agent, contractor, and property manager.', src: 'fed1929' },
  { id: 'F13', item: 'Capital-gain rates applied to sale proceeds (20% federal top rate, 3.8% NIIT, CA 12.30% plus 1% MHS)', why: 'CA rates verified. 20% federal rate and 3.8% NIIT not fetched.', need: 'Fetch IRC §1(h), §1411, and the 2026 Schedule D instructions.', src: 'irc1411' },
  { id: 'F14', item: 'Principal-residence exclusion of $250,000 (single filer)', why: 'IRC §121 not fetched.', need: 'Fetch IRC §121 and confirm joint filing and eligibility.', src: 'irc121' },
  { id: 'F15', item: 'Cash and Treasury yields (4.5% used for parked cash)', why: 'Treasury curve not fetched. Earlier secondary yields were not used.', need: 'Fetch Treasury daily par yield curve for the transfer date.', src: 'treasury' },
  { id: 'F16', item: 'City transfer tax on Property A (the city)', why: 'Not verified. Set to zero in the model.', need: 'Confirm with the city.', src: 'sfTT' },
  { id: 'F17', item: 'SF transfer tax rate and pending ordinance (File 260178) and Prop I (Nov 2026)', why: 'sf.gov transfer-tax page failed to fetch. Ordinance and Prop I not enacted or certified.', need: 'Fetch sf.gov transfer-tax page after Prop I certification.', src: 'sfTT' },
  { id: 'F18', item: 'Prop H (Nov 2026) certification', why: 'Results are preliminary (sfelections.org, updated 11/23/2026).', need: 'Check final certified results.', src: 'sfElec' },
  { id: 'F19', item: 'SFPUC line items (service charge, tiers)', why: 'Only summary bill figures verified.', need: 'Fetch the SFPUC rate schedule once the rates-and-fees page works.', src: 'sfPUC' },
  { id: 'F20', item: 'Black-swan timing and recovery lengths (2008 trough 17 mo; 2008 back 48 mo; 1929 trough 34 mo)', why: 'Drop sizes verified; timing and recovery lengths are illustrative assumptions.', need: 'Replace with verified index history if the model is re-run.', src: 'fed1929' },
  { id: 'F21', item: 'Home-price drawdown of 30% (2008-type)', why: 'Taken from a search snippet; the Fed History essay returned 404.', need: 'Confirm from a primary index (for example FHFA or Case-Shiller).', src: 'fed1929' },
  { id: 'F22', item: 'Monte Carlo ranges and crash probability (10%)', why: 'Analyst assumptions, not forecasts.', need: 'Review with the household and CPA.', src: 'ssaLRA' },
  { id: 'F23', item: 'Stagflation scenario (5% CPI, 0.5% home growth, 3% equities)', why: 'Illustrative. Not sourced to an official forecast.', need: 'Keep as a stress test only.', src: 'ssa2026' },
  { id: 'F24', item: 'Interpretation: Rule 3 also applied to path E (mixed)', why: 'DECISION_RULES.md names A and F only. E includes occupancy, so it is treated the same way.', need: 'Log as an interpretation in COORDINATION.md; household to confirm.', src: 'lta26026' },
  { id: 'F25', item: 'Interpretation: second tie-break (regulatory exposure) order C, D24, D36, then occupancy paths', why: 'Rule 8 names the tie-break but not how to rank exposure.', need: 'Logged in COORDINATION.md. Household and CPA to confirm.', src: 'lta26026' },
  { id: 'F26', item: 'Estate-tax 40% top rate (IRC §2001)', why: 'Secondary only.', need: 'Fetch IRC §2001 or Form 706 instructions.', src: 'i706' },
  { id: 'F27', item: 'Replacement housing cost for sale paths', why: 'Model does not charge replacement housing to C, D, or the sale part of F. Rule 3 values imputed rent for occupancy paths only.', need: 'Household to state its housing need; re-run.', src: 'fed1929' },
];

// Deadlines and dates. Every row has a source key; dates marked (secondary) are not primary-confirmed.
const TIMELINE = [
  { when: 'Within 40 days after death', what: 'Small-estate affidavit window (if eligible; threshold $166,250)', src: 'prob13100', status: 'verified' },
  { when: 'Within 9 months after death', what: 'Form 706 filing (if required)', src: 'i706', status: 'FLAGGED: secondary only (F01)' },
  { when: 'Within 1 year of transfer', what: 'Child occupies as principal residence and claims homeowners\u2019 exemption for Prop 19', src: 'lta26026', status: 'verified (chunks 0-2)' },
  { when: 'Within 3 years of transfer, or before a third-party transfer', what: 'File Prop 19 intergenerational claim', src: 'lta26026', status: 'verified (chunks 0-2)' },
  { when: 'Apr 15, 2026 (past)', what: '2025 Form 540 due; estimated payment 1', src: 'ftb540', status: 'verified' },
  { when: 'Jun 15, 2026 (past)', what: '2026 estimated payment 2', src: 'ftb540', status: 'verified' },
  { when: 'Jul 1, 2026 (past)', what: 'SFPUC water +7.0% and sewer +15.0%', src: 'sfPUC', status: 'verified' },
  { when: 'Sep 15, 2026 (past)', what: '2026 estimated payment 3', src: 'ftb540', status: 'verified' },
  { when: 'Oct 15, 2026 (past)', what: 'Extended 2025 Form 540 due date', src: 'ftb540', status: 'verified' },
  { when: 'Jan 15, 2027', what: '2026 estimated payment 4', src: 'ftb540', status: 'verified' },
  { when: 'Feb 16, 2027', what: 'Prop 19 indexed amount next adjustment (currently $1,044,586)', src: 'lta25009', status: 'verified' },
  { when: 'Mar 1, 2027', what: 'SF rent-controlled increase 2.3% effective 3/1/2027 (applies to rent-controlled units only)', src: 'sfRent', status: 'verified' },
  { when: 'Jul 1, 2027', what: 'SF Prop H parcel tax begins (preliminary; certification pending)', src: 'sfVIP', status: 'verified (terms); passage preliminary' },
  { when: 'Within 5 years of death', what: 'Late portability election for the deceased spouse (if applicable)', src: 'revproc', status: 'FLAGGED: secondary (F03)' },
];

const GLOSSARY = [
  ['Basic exclusion amount', 'Federal estate and gift exemption. $15,000,000 for 2026.', 'revproc'],
  ['Basis (stepped-up)', 'Tax cost of inherited property, generally fair market value at date of death.', 'pub551'],
  ['Black swan', 'A rare, severe market shock. Here: 1929-type and 2008-type crashes, modelled as illustrations.', 'fed1929'],
  ['CCPI / Prop 13 factor', 'Annual cap on growth of the base-year value (2026-27: 1.02).', 'lta26002'],
  ['Documentary transfer tax', 'County tax on recorded sales ($0.55 per $500).', 'rtc11911'],
  ['Depreciation and recapture', 'Deduction for wear on rental property, reclaimed on sale. Basis rules in Pub. 551.', 'pub551'],
  ['Factored base year value', 'Prior assessed value adjusted by the Prop 13 factor; base for Prop 19.', 'boeProp19'],
  ['Fair market value (FMV)', 'Price a willing buyer and seller would agree on. Needs a written valuation at date of death.', 'irsEstate'],
  ['Imputed rent', 'Value of living in a home you own, equal to rent you would otherwise pay (model: occupied share only).', 'fed1929'],
  ['Indexed amount (Prop 19)', '$1,044,586 for transfers 2/16/2025 to 2/15/2027 (BOE).', 'lta25009'],
  ['Mixed path (E)', 'Occupy part of a property and rent the rest.', 'boeProp19'],
  ['Monte Carlo', 'Repeated random draws across stated ranges to show a spread of outcomes.', 'ssaLRA'],
  ['Parent-child exclusion (Prop 19)', 'Base-year transfer exclusion for a child who occupies the home as principal residence.', 'boeProp19'],
  ['Phased investing', 'Holding proceeds in cash or Treasury bills, then moving them into equities over several months.', 'treasury'],
  ['Primary metric', 'Median real (CPI-deflated) net position at the horizon (DECISION_RULES.md §2).', 'ssa2026'],
  ['Principal residence', 'Home the owner lives in as their main home (sale exclusion and Prop 19 eligibility).', 'boeProp19'],
  ['Real value', 'Value after removing inflation, using CPI for the scenario.', 'blsCpi'],
  ['Rate tax area (TRA)', 'Area with its own tax rate set by local bonds and levies. Confirm for Property A.', 'scTax'],
  ['Reassessment', 'Re-setting a property\u2019s taxable value to market value after a change of ownership or use.', 'boeProp19'],
  ['Small-estate affidavit', 'California shortcut for estates under the threshold ($166,250).', 'prob13100'],
  ['Step-up in basis', 'See Basis (stepped-up).', 'pub551'],
  ['Tie rule', 'If two paths are within 2% on the primary metric, prefer more liquidity, then lower regulatory exposure.', 'revproc'],
  ['Treasury bills (3M to 2Y)', 'Short-term US government debt used for parked cash in the phased path.', 'treasury'],
];

const SUGGESTIONS = [
  'Obtain the verified base-year value for Property A from the County Assessor and enter it in the model (kept out of publication).',
  'Get a written date-of-death appraisal before any decision; the valuation sets the basis, the estate value, and the Prop 19 baseline.',
  'Ask an estate attorney to confirm the trust structure, the Prop 19 claim path (one-year occupancy and three-year claim), and any §1031 options before any sale.',
  'Ask a CPA to model depreciation recapture and the §121 exclusion for any part of Property A used as a rental.',
  'Collect three verified rental comparables and a landlord-policy quote before choosing path B.',
  'Set the liquidity reserve in months of household spending before proceeds arrive; the investing policy has a placeholder.',
  'Re-run the model yearly and after each change listed in DECISION_RULES.md §4.',
  'Keep Property B inputs and any household figures out of any public repository.',
];

module.exports = { SOURCES, FLAGGED, TIMELINE, GLOSSARY, SUGGESTIONS };
