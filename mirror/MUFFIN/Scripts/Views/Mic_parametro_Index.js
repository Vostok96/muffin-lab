
var tabladata;
$(document).ready(function () {


    activarMenu("Mantenedor_con");

    ////validamos el formulario
    $("#form").validate({
        rules: {
            txtCod: "required",
            txtDesc: "required",

            cboTipo: "required",
            txtHtml: "required",

            cboSeccion: "required",
            txtMetodologia: "required",
            txtUnidadMedida: "required"
        },
        messages: {
            txtCod: "(*)",
            txtDesc: "(*)",

            cboTipo: "(*)",
            txtHtml: "(*)",

            cboSeccion: "(*)",
            txtMetodologia: "(*)",
            txtUnidadMedida: "(*)"
        },
        errorElement: 'span'
    });

    tabladata = $('#tbdata').DataTable({
        "ajax": {
            "url": $.MisUrls.url._ObtenerMic_parametro,
            "type": "GET",
            "datatype": "json"
        },
        "columns": [
            { "data": "parametro_cod" },
            { "data": "parametro_desc" },
            { "data": "parametro_seccion" },
            {
                "data": "parametro_tipo", "render": function (data) {
                    if (data =="COMBO_BOX") {
                        return '<span class="badge badge-success">LISTA DE OPCIONES</span>'
                    } if (data == "TEXT") {
                        return '<span class="badge badge-success">CAMPO DE TEXTO</span>'
                    } if (data == "TEXT_AREA") {
                        return '<span class="badge badge-success">AREA DE TEXTO</span>'
                    } if (data == "TEXT_DATE") {
                        return '<span class="badge badge-success">FECHA</span>'
                    } if (data == "TEXT_DATIME") {
                        return '<span class="badge badge-success">FECHA Y HORA</span>'
                    }

                    if (data == "") {
                        return 'LABORATORIO'
                    }
                }
            },
            {
                "data": "parametro_id", "render": function (data, type, row, meta) {
                    return "<button class='btn btn-primary btn-sm' type='button' onclick='abrirPopUpForm(" + JSON.stringify(row) + ")'><i class='fas fa-pen'></i></button>";                        
                },
                "orderable": false,
                "searchable": false,
                "width": "90px"
            }

        ],
        "language": {
            "url": $.MisUrls.url.Url_datatable_spanish
        },
        responsive: true
    });


    $('#cboSeccion').change(function () {
        idSelec = $(this).val();
        if (idSelec == "MICROBIOLOGIA") {
            $('#div_micro').show();
            $('#div_laboratorio').hide();
        }
        if (idSelec == "LABORATORIO") {
            $('#div_laboratorio').show();
            $('#div_micro').hide();
        }
    });
})


function abrirPopUpForm(json) {
    $("#txtid").val(0);
    if (json != null) {
        $("#txtid").val(json.parametro_id);
        $("#txtCod").val(json.parametro_cod);
        $("#txtDesc").val(json.parametro_desc);
        $("#txtResFav").val(json.parametro_res_fav);

        $("#cboTipo").val(json.parametro_tipo);
        $("#txtHtml").val(json.parametro_html);

        $("#cboSeccion").val(json.parametro_seccion);
        $("#txtMetodologia").val(json.parametro_metodologia);
        $("#txtUnidadMedida").val(json.parametro_unidad);
        $("#txtValRef1").val(json.parametro_val_ref1);
        $("#txtValRef2").val(json.parametro_val_ref2);
        $("#txtValRefTexto").val(json.parametro_val_texto);

        $("#txtCod").prop("disabled", true);

        if (json.parametro_seccion == "MICROBIOLOGIA") {
            $('#div_micro').show();
            $('#div_laboratorio').hide();
        }
        if (json.parametro_seccion == "LABORATORIO") {
            $('#div_laboratorio').show();
            $('#div_micro').hide();
        }
    } else {
        $("#form").each(function () {
            this.reset();
        });
        //EL PRIMER COMBO MICRO
        $('#div_micro').show();
        $('#div_laboratorio').hide();

        $("#txtCod").prop("disabled", false);
    }    
    $('#FormModal').modal('show');
}


function Guardar() {

    if ($("#form").valid()) {
        var request = null;
        if ($("#cboSeccion").val() == "MICROBIOLOGIA") {
            request = {
                objeto: {
                    parametro_seccion: $("#cboSeccion").val(),
                    parametro_id: $("#txtid").val(),
                    parametro_cod: $("#txtCod").val(),
                    parametro_desc: $("#txtDesc").val(),
                    parametro_res_fav: $("#txtResFav").val(),

                    parametro_tipo: $("#cboTipo").val(),
                    parametro_html: $("#txtHtml").val(),
                    
                    parametro_metodologia:"",
                    parametro_unidad:"",
                    parametro_val_ref1:"",
                    parametro_val_ref2:"",
                    parametro_val_texto:"",
                }
            }
        }
        if ($("#cboSeccion").val() == "LABORATORIO") {
            request = {
                objeto: {
                    parametro_seccion: $("#cboSeccion").val(),
                    parametro_id: $("#txtid").val(),
                    parametro_cod: $("#txtCod").val(),
                    parametro_desc: $("#txtDesc").val(),
                    parametro_res_fav: $("#txtResFav").val(),

                    parametro_tipo: "",
                    parametro_html: "",

                    parametro_metodologia:$("#txtMetodologia").val(),
                    parametro_unidad:$("#txtUnidadMedida").val(),
                    parametro_val_ref1:$("#txtValRef1").val(),
                    parametro_val_ref2:$("#txtValRef2").val(),
                    parametro_val_texto:$("#txtValRefTexto").val()
                }
            }
        }

        console.log(request);
        jQuery.ajax({
            url: $.MisUrls.url._GuardarMic_parametro,
            type: "POST",
            data: JSON.stringify(request),
            dataType: "json",
            contentType: "application/json; charset=utf-8",
            success: function (data) {
                if (data.resultado) {
                    tabladata.ajax.reload();
                    $('#FormModal').modal('hide');
                } else {
                    swal("Mensaje", "No se pudo guardar los cambios", "warning")
                }
            },
            error: function (error) {
                console.log(error)
            },
            beforeSend: function () {

            },
        });
    }

}

