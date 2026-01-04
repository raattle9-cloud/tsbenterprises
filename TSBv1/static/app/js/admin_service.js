document.addEventListener('DOMContentLoaded', function () {
    const advanceCheckbox = document.getElementById('id_supports_advance_payment');
    const advanceTypeField = document.querySelector('.field-advance_payment_type');
    const advanceValueField = document.querySelector('.field-advance_payment_value');

    function toggleAdvanceFields() {
        if (advanceCheckbox.checked) {
            advanceTypeField.style.display = 'block';
            advanceValueField.style.display = 'block';
        } else {
            advanceTypeField.style.display = 'none';
            advanceValueField.style.display = 'none';
        }
    }

    if (advanceCheckbox && advanceTypeField && advanceValueField) {
        advanceCheckbox.addEventListener('change', toggleAdvanceFields);
        toggleAdvanceFields(); // Initial state
    }
});
