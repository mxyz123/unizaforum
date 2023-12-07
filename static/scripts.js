function showNav() {
            if ( document.getElementById("toggleNavTarget").classList.contains('show') ){
                document.getElementById("toggleNavTarget").classList.remove('show');
            } else {
                document.getElementById("toggleNavTarget").classList.add('show');
            }
        }

function login() {
    if (document.getElementById("email").value == "") {
        error_handler(1);
        return;
    }
    if (document.getElementById("password").value == "") {
        error_handler(2);
        return;
    }
    document.getElementById("logForm").submit();
}

function register() {
    if (document.getElementById("meno").value == "") {
        error_handler(0);
        return;
    }
    if (document.getElementById("email").value == "") {
        error_handler(1);
        return;
    }
    if (document.getElementById("email").matches.call(document.getElementById("email"), ':invalid')) {
        error_handler(11);
        return;
    }
    if (document.getElementById("password").value == "") {
        error_handler(2);
        return;
    }
    if (!(document.getElementById("password").value == document.getElementById("password2").value)) {
        error_handler(3);
        return;
    }
    document.getElementById("regForm").submit();
}

function deleteUser(username) {
    window.location.href = document.location.origin + "/admin/delete/" + username;
}

function editBtn(username) {
    window.location.href = document.location.origin + "/profile/edit";
}

function editProfile() {
    if (document.getElementById("pswd").value != "" && document.getElementById("newPswd").value == "") {
        error_handler(2);
        return;
    }
    if ( document.getElementById("password").value != "" &&
    !(document.getElementById("password").value == document.getElementById("password2").value)) {
        error_handler(3);
        return;
    }
    if (document.getElementById("file").files.length > 0) {
        let pfp = document.getElementById("file").files[0].name;
        let ext = pfp.substring(pfp.lastIndexOf('.')+1, pfp.length) || pfp;
        switch (ext.toLowerCase()) {
            case 'png':
            case 'jpg':
            case 'jpeg':
            case 'gif':
                break;
            default:
                error_handler(10);
                return;
        }
    }
    document.getElementById("editForm").submit();
}

function error_handler(err_code) {
    switch (err_code) {
        case 0:
            alert("Meno nemôže byť prázdne!");
            break;
        case 1:
            alert("E-mail nemôže byť prázdny!");
            break;
        case 2:
            alert("Heslo nemôže byť prázdne!");
            break;
        case 3:
            alert("Heslá sa musia zhodovať!");
            break;
        case 4:
            alert("Dané meno sa už používa!");
            break;
        case 5:
            alert("Daný e-mail sa už používa!");
            break;
        case 6:
            alert("Nesprávne prihlasovacie údaje!")
            break;
        case 7:
            alert("Prihlásenie prebehlo úspešne!")
            break;
        case 8:
            alert("Registrácia prebehla úspešne!")
            break;
        case 9:
            alert("Účet je už prihlásený!")
            break;
        case 10:
            alert("Nepodporovaný typ súboru!")
            break;
        case 11:
            alert("Naplatný e-mail!")
            break;
        default:
            alert("Chyba!")
            return;
    }
}