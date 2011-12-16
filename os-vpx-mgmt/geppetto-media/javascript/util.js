function submit_form_with_action_value(value, form, wait_text){
    document.getElementById("action") = value;
    submit_form(form, wait_text)
}
function prepareToSubmit(wait_text){
    if(wait_text)
        showPopWin(135, 35, wait_text);
    else
        showPopWin(135, 35, 'Submitting...');
}

function submit_form(form, wait_text){
    prepareToSubmit(wait_text);
    setTimeout(function (){
        document.getElementById(form).submit();
    }, 300);
}
function powerButton(form, uuid, vm_name, pool_id, action,wait_text){
    document.getElementById('VMActionUUID').value = uuid;
    document.getElementById('VMActionVMName').value = vm_name;
    document.getElementById('VMActionPoolId').value = pool_id;
    document.getElementById('VMActionAction').value = action;
    submit_form(form,wait_text);
}
function shareButton(form, user_name, user_id, action, wait_text){
    document.getElementById('VMEditTagUser').value = user_name;
    document.getElementById('VMEditTagUserID').value = user_id;
    document.getElementById('VMEditTagAction').value = action;
    submit_form(form, wait_text);
}
function shareRecentButton(form, user_name, user_id, vm_uuid, vm_name, pool_id, wait_text){
    document.getElementById('VMEditTagUser').value = user_name;
    document.getElementById('VMEditTagUserID').value = user_id;
    document.getElementById('VMEditTagUUID').value = vm_uuid;
    document.getElementById('VMEditTagVMName').value = vm_name;
    document.getElementById('VMEditTagPoolId').value = pool_id;
    submit_form(form, wait_text);
}
function clearTextBox(textBox){
    document.getElementById(textBox).value = "";
}