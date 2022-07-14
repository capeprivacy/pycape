use hacspec_lib::{Seq, U8};
use hpke::{AdditionalData, HPKECiphertext, HPKEConfig, HpkePublicKey, HpkeSeal, Mode};
use hpke_aead::AEAD;
use hpke_errors::HpkeError;
use hpke_kdf::{Info, KDF};
use hpke_kem::{Randomness, KEM};
use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;
use pyo3::types::PyBytes;
use rand::{rngs::OsRng, RngCore};

fn get_default_hpke_config() -> HPKEConfig {
    let mode = Mode::mode_base;
    let kem = KEM::DHKEM_X25519_HKDF_SHA256;
    let kdf = KDF::HKDF_SHA256;
    let aead = AEAD::ChaCha20Poly1305;
    HPKEConfig(mode, kem, kdf, aead)
}

fn hpke_seal_bytes(pkb: &[u8], ptxtb: &[u8]) -> Result<Vec<u8>, HpkeError> {
    let hpke_config = get_default_hpke_config();
    let pk = HpkePublicKey::from_public_slice(pkb);
    let ptxt = Seq::<U8>::from_public_slice(ptxtb);
    let info = Info::new(0);
    let aad = AdditionalData::new(0);
    let mut rand_bytes = [0u8; 32];
    OsRng.fill_bytes(&mut rand_bytes);
    let randomness = Randomness::from_public_slice(&rand_bytes);
    let result: HPKECiphertext = HpkeSeal(
        hpke_config,
        &pk,
        &info,
        &aad,
        &ptxt,
        None,
        None,
        None,
        randomness,
    )?;
    let ciphertext = result.1;
    Ok(ciphertext.into_native())
}

/// Python binding to hpke-spec's Single-Shot API function hpke::HpkeSeal
#[pyfunction]
fn hpke_seal<'p>(py: Python<'p>, pk_py: &PyBytes, ptxt_py: &PyBytes) -> PyResult<&'p PyBytes> {
    let pkb = pk_py.as_bytes();
    let ptxtb = ptxt_py.as_bytes();
    let ciphertext_bytes = hpke_seal_bytes(pkb, ptxtb)
        .map_err(|hpke_error| PyRuntimeError::new_err(format!("{hpke_error:?}")))?;
    Ok(PyBytes::new(py, &ciphertext_bytes))
}

/// A Python module implemented in Rust.
#[pymodule]
fn hpke_spec(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(hpke_seal, m)?)?;
    Ok(())
}
