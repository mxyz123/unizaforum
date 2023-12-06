function showNav() {
            if ( document.getElementById("toggleNavTarget").classList.contains('show') ){
                document.getElementById("toggleNavTarget").classList.remove('show');
            } else {
                document.getElementById("toggleNavTarget").classList.add('show');
            }
        }

function register() {
    if (document.getElementById("meno").value == "") {
        alert("Meno nemôže byť prázdne!");
        return;
    }
    if (document.getElementById("email").value == "") {
        alert("E-mail nemôže byť prázdny!");
        return;
    }
    if (document.getElementById("password").value == "") {
        alert("Heslo nemôže byť prázdne!");
        return;
    }
    if (!(document.getElementById("password").value == document.getElementById("password2").value)) {
        alert("Heslá sa musia zhodovať!");
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