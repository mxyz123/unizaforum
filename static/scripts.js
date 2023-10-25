function showNav() {
            if ( document.getElementById("toggleNavTarget").classList.contains('show') ){
                document.getElementById("toggleNavTarget").classList.remove('show');
            } else {
                document.getElementById("toggleNavTarget").classList.add('show');
            }
        }