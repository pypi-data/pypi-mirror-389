class CompanyInfo {
  name string @description("Company's legal name")
  description string @description("What the company does")
  founders string[] @description("List of founder names")
  funding string | null @description("Total funding raised (optional)")
}

function ExtractCompanyInfo(research_output: string) -> CompanyInfo {
  client CustomGPT4o
  prompt #"
    Extract company information from the research:

    {{ research_output }}

    {{ ctx.output_format }}
  "#
}

function ExtractCompanyFinancials(research_output: string) -> CompanyInfo {
  client CustomGPT4o
  prompt #"
    You are a financial analyst. Focus on financial metrics and revenue models.

    {{ research_output }}

    {{ ctx.output_format }}
  "#
}
