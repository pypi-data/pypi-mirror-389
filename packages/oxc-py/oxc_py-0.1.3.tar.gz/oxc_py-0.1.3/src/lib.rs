use pyo3::prelude::*;

use std::io::Write;
use tempfile::NamedTempFile;

use oxc_allocator::Allocator;
use oxc_codegen::CodeGenerator;
use oxc_parser::Parser;
use oxc_semantic::SemanticBuilder;
use oxc_span::SourceType;
use oxc_transformer::{HelperLoaderMode, JsxRuntime, TransformOptions, Transformer};

fn create_temp_file(content: &str) -> NamedTempFile {
    let mut temp = NamedTempFile::new().expect("Failed to create temp file");
    writeln!(temp, "{}", content).expect("Failed to write to temp file");
    return temp;
}

trait TransformerFromString<'a> {
    fn from_string(allocator: &'a Allocator, source_text: &str, options: &TransformOptions) -> Self;
}

impl<'a> TransformerFromString<'a> for Transformer<'a> {
    fn from_string(allocator: &'a Allocator, source_text: &str, options: &TransformOptions) -> Self {
        let temp_file = create_temp_file(source_text);
        let temp_path = temp_file.path();
        Self::new(allocator, temp_path, options)
    }
}

// Adapted from https://github.com/oxc-project/oxc/blob/71155cf575b6947bb0e85376d18375c2f3c50c73/crates/oxc_transformer/examples/transformer.rs
fn transform_jsx(source_text: &str) -> String {
    let allocator = Allocator::default();
    let source_type = SourceType::jsx();

    let ret = Parser::new(&allocator, &source_text, source_type).parse();

    if !ret.errors.is_empty() {
        println!("Parser Errors:");
        for error in ret.errors {
            let error = error.with_source_code(source_text.to_string());
            println!("{error:?}");
        }
    }

    //println!("Original:\n");
    //println!("{source_text}\n");

    let mut program = ret.program;

    let ret = SemanticBuilder::new()
        // Estimate transformer will triple scopes, symbols, references
        .with_excess_capacity(2.0)
        .build(&program);

    if !ret.errors.is_empty() {
        println!("Semantic Errors:");
        for error in ret.errors {
            let error = error.with_source_code(source_text.to_string());
            println!("{error:?}");
        }
    }

    let (symbols, scopes) = ret.semantic.into_symbol_table_and_scope_tree();

    let mut transform_options = TransformOptions::from_target("esnext").unwrap();
    transform_options.helper_loader.mode = HelperLoaderMode::External;
    transform_options.jsx.runtime = JsxRuntime::Classic;

    let ret = Transformer::from_string(&allocator, &source_text, &transform_options).build_with_symbols_and_scopes(
        symbols,
        scopes,
        &mut program,
    );

    if !ret.errors.is_empty() {
        println!("Transformer Errors:");
        for error in ret.errors {
            let error = error.with_source_code(source_text.to_string());
            println!("{error:?}");
        }
    }

    let printed = CodeGenerator::new().build(&program).code;
    //println!("Transformed:\n");
    //println!("{printed}");

    return printed.to_string();
}


/// Transforms JSX string to JS string.
#[pyfunction]
fn transform(source_text: String) -> PyResult<String> {
    let source_str = source_text.to_string();
    Ok(transform_jsx(&source_str).to_string())
}

/// A Python module implemented in Rust.
#[pymodule]
fn oxc_py(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(transform, m)?)?;
    Ok(())
}

fn main() {
    // No-op
}

