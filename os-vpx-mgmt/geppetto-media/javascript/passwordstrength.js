function passwordChanged(password_field, strength_div, strength_field) {
    var strength = document.getElementById(strength_div);
    var strongRegex = new XRegExp("^(?=.{11,})(?=.*\\p{L})(?=.*[0-9]).*$", "g");
    var mediumRegex = new XRegExp("^(?=.{8,})(((?=.*\\p{L})(?=.*[0-9]))).*$", "g");
    var enoughRegex = new RegExp("(?=.{6,}).*", "g");
    var pwd = document.getElementById(password_field);
    if (pwd.value.length==0) {
        strength.innerHTML = '<span style="color:red">Weak</span>';
        document.getElementById(strength_field).value = "0";
    } else if (false == enoughRegex.test(pwd.value)) {
        strength.innerHTML = '<span style="color:red">Weak</span>';
        document.getElementById(strength_field).value = "1";
    } else if (strongRegex.test(pwd.value)) {
        strength.innerHTML = '<span style="color:green">Strong</span>';
        document.getElementById(strength_field).value = "3";
    } else if (mediumRegex.test(pwd.value)) {
        strength.innerHTML = '<span style="color:orange">Medium</span>';
        document.getElementById(strength_field).value = "2";
    }  else {
        strength.innerHTML = '<span style="color:red">Weak</span>';
        document.getElementById(strength_field).value = "1";
    }
}