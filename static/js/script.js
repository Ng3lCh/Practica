function jsValidarUsuario(){

    let Usuario = $("#Correo").val().trim();
    let Clave = $("#Contrasena").val();

    if(!Usuario || !Clave){

        mostrarMensaje(
            "Completa usuario y contraseña",
            "#ef4444"
        );

        return;
    }

    let datos = new FormData();

    datos.append("Usuario", Usuario);
    datos.append("Clave", Clave);

    $(".login .btn-oneparfum").prop("disabled", true);

    $.ajax({

        url: RUTA_CONSULTAS,

        type: "POST",

        data: datos,

        contentType: false,

        processData: false,

        dataType: "json",

        success: function(r){

            if(r.Respuesta == "OK"){

                window.location.href =
                    BASE_URL + r.redirect;

            }else{

                mostrarMensaje(
                    "Usuario o contraseña incorrectos",
                    "#ef4444"
                );

                $(".login .btn-oneparfum").prop("disabled", false);

            }

        },

        error: function(xhr){

            console.log(xhr.responseText);

            mostrarMensaje(
                "Error en el servidor",
                "#ef4444"
            );

            $(".login .btn-oneparfum").prop("disabled", false);

        }

    });
}


function mostrarMensaje(texto, color){

    $("#mensajeLogin")
        .text(texto)
        .css("color", color);

}


// Captura Enter dentro de los campos de login (el form no tiene action/method)
$(document).on("keypress", "#formLogin input", function(e){

    if(e.which === 13){

        e.preventDefault();
        jsValidarUsuario();

    }

});