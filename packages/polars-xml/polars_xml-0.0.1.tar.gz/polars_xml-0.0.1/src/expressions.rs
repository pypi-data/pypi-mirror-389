use polars::prelude::*;
use pyo3_polars::derive::polars_expr;
use serde::Deserialize;

fn xpath_str<'a>(
	input: &'a str,
	xpath: &str,
	output: &mut String,
) -> Result<(), PolarsError> {
	use sxd_document::parser;

	let package =
		parser::parse(input).map_err(|e| polars_err!(ComputeError: "{}", e))?;
	let document = package.as_document();
	*output = sxd_xpath::evaluate_xpath(&document, xpath)
		.map_err(|e| polars_err!(ComputeError: "{}", e))?
		.into_string();
	Ok(())
}

#[derive(Deserialize)]
struct XPathKwargs {
	xpath: String,
}

#[polars_expr(output_type=String)]
fn xpath(inputs: &[Series], kwargs: XPathKwargs) -> PolarsResult<Series> {
	let ca = inputs[0].str()?;
	let out: StringChunked =
		ca.try_apply_into_string_amortized(|value, output| {
			xpath_str(value, &kwargs.xpath, output)
		})?;
	Ok(out.into_series())
}
