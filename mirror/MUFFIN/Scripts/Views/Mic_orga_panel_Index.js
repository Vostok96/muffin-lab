
var tabladata;
$(document).ready(function () {


    activarMenu("Mantenedor_con");


    ////validamos el formulario
    $("#form").validate({
        rules: {
            txtOrden: "required",
            txtDesc: "required"
        },
        messages: {
            txtOrden: "(*)",
            txtDesc: "(*)"
        },
        errorElement: 'span'
    });

    tabladata = $('#tbdata').DataTable({
        "ajax": {
            "url": $.MisUrls.url._ObtenerMic_orga_panel,
            "type": "GET",
            "datatype": "json"
        },
        "columns": [
            { "data": "orga_panel_desc" },
            { "data": "orga_panel_orden" },
            {
                "data": "orga_panel_id", "render": function (data, type, row, meta) {
                    return "<button class='btn btn-primary btn-sm' type='button' onclick='abrirPopUpForm(" + JSON.stringify(row) + ")'><i class='fas fa-pen'></i></button>"
                        + " <button class='btn btn-primary btn-sm' type='button' onclick='abrirPopUpForm_DET(" + JSON.stringify(row) + ")'><i class='fas fa-align-left'></i></button>"
                        + " <button class='btn btn-danger btn-sm' type='button' onclick='_EliminarMic_orga_panel(" + row.orga_panel_id + ")'><i class='fa fa-trash'></i></button>";
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


    $("#btnAddATB").click(function () {
        $("#formATB").each(function () {
            this.reset();
            $("#txtATBId").val(0);
        });
        $('#FormModal_ATB').modal('show');
        _ObtenerMic_antibiotico(0);
    });

    $('tbody#tlbtbodyDet').on('click', 'button.btn-primary', function () {
        json_val = $(this).attr('value');
        var json = JSON.parse(json_val);

        $('#FormModal_ATB').modal('show');

        $("#txtATBId").val(json.atb_id);
        $("#cboATBInterpretacion").val(json.orga_panel_det_interpretacion);
        $("#txtATBOrden").val(json.orga_panel_det_orden);

        _ObtenerMic_antibiotico(json.atb_id);
    });

})


function abrirPopUpForm(json) {
    if (json != null) {
        $("#txtid").val(json.orga_panel_id);
        $("#txtDesc").val(json.orga_panel_desc);
        $("#txtOrden").val(json.orga_panel_orden);
    } else {
        $("#form").each(function () {
            this.reset();
            $("#txtid").val(0);
        });
    }
    $('#FormModal').modal('show');
}


function abrirPopUpForm_DET(json) {
    if (json != null) {
        $("#txtDet_id").val(json.orga_panel_id);
        $("#txtDet_desc").val(json.orga_panel_desc);
        _ObtenerMic_orga_panel_detalle(json.orga_panel_id);
    } else {

    }
    $('#FormModal_DET').modal('show');
}


function _ObtenerMic_orga_panel_detalle(orga_panel_id) {
    //OBTENER 
    jQuery.ajax({
        url: $.MisUrls.url._ObtenerMic_orga_panel_detalle + "?orga_panel_id=" + orga_panel_id,
        type: "GET",
        dataType: "json",
        contentType: "application/json; charset=utf-8",
        success: function (data) {
            if (data.data != null) {
                html = '';
                $.each(data.data, function (i, item) {
                    html += '<tr>';
                    html += '<td>' + item.oMic_antibiotico.atb_desc + '</td>';
                    html += '<td>' + item.orga_panel_det_interpretacion + '</td>';
                    html += '<td>' + item.orga_panel_det_orden + '</td>';
                    html += "<td><button class='btn btn-primary btn-sm' type='button' value='" + JSON.stringify(item) + "'><i class='fas fa-pen'></i></button>";
                    html += ' <button class="btn btn-danger btn-sm ml-2" type="button" onclick="_EliminarMic_orga_panel_detalle(' + item.orga_panel_det_id + ')"><i class="fa fa-trash"></i></button></td>';
                    html += '</tr>';
                });
                $("#tlbtbodyDet").html(html);
            }
        },
        error: function (error) {
            console.log(error)
        },
        beforeSend: function () {
        },
    });
} 

function _ObtenerMic_antibiotico(selectec) {
    //OBTENER MUESTRA
    jQuery.ajax({
        url: $.MisUrls.url._ObtenerMic_antibiotico,
        type: "GET",
        dataType: "json",
        contentType: "application/json; charset=utf-8",
        success: function (data) {
            $("#cboATBDesc").html("");
            if (data.data != null) {
                $.each(data.data, function (i, item) {
                    $("<option>").attr({ "value": item.atb_id }).text(item.atb_desc).appendTo("#cboATBDesc");
                })
                if (selectec == 0) {
                    $("#cboATBDesc option:first").val()
                } else {
                    $("#cboATBDesc").val(selectec);
                }
            }
        },
        error: function (error) {
            console.log(error)
        },
        beforeSend: function () {
        },
    });
} 


function Guardar() {
    if ($("#form").valid()) {

        var request = {
            objeto: {
                orga_panel_id: $("#txtid").val(),
                orga_panel_desc: $("#txtDesc").val(),
                orga_panel_orden: $("#txtOrden").val()
            }
        }
        jQuery.ajax({
            url: $.MisUrls.url._GuardarMic_orga_panel,
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


function _GuardarMic_orga_panel_detalle() {
    if ($("#formATB").valid()) {

        var request = {
            objeto: {
                orga_panel_det_id: $("#txtATBId").val(),
                atb_id: $("#cboATBDesc").val(),
                orga_panel_det_interpretacion: $("#cboATBInterpretacion").val(),
                orga_panel_det_orden: $("#txtATBOrden").val(),
                orga_panel_id: $("#txtDet_id").val()
            }
        }
        jQuery.ajax({
            url: $.MisUrls.url._GuardarMic_orga_panel_detalle,
            type: "POST",
            data: JSON.stringify(request),
            dataType: "json",
            contentType: "application/json; charset=utf-8",
            success: function (data) {
                if (data.resultado) {
                    _ObtenerMic_orga_panel_detalle($("#txtDet_id").val());
                    $('#FormModal_ATB').modal('hide');
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


function _EliminarMic_orga_panel($orga_panel_id) {
    swal({
        title: "Mensaje",
        text: "¿Desea eliminar el registro seleccionado?",
        type: "warning",
        showCancelButton: true,

        confirmButtonText: "Sí",
        confirmButtonColor: "#DD6B55",

        cancelButtonText: "No",

        closeOnConfirm: true
    },

        function () {
            jQuery.ajax({
                url: $.MisUrls.url._EliminarMic_orga_panel + "?orga_panel_id=" + $orga_panel_id,
                type: "GET",
                dataType: "json",
                contentType: "application/json; charset=utf-8",
                success: function (data) {
                    if (data.resultado) {
                        tabladata.ajax.reload();
                    } else {
                        swal("Mensaje", "No se pudo eliminar el registro seleccionado", "warning")
                    }
                },
                error: function (error) {
                    console.log(error)
                },
                beforeSend: function () {

                },
            });
        });
}


function _EliminarMic_orga_panel_detalle($orga_panel_det_id) {
    swal({
        title: "Mensaje",
        text: "¿Desea eliminar el registro seleccionado?",
        type: "warning",
        showCancelButton: true,

        confirmButtonText: "Sí",
        confirmButtonColor: "#DD6B55",

        cancelButtonText: "No",

        closeOnConfirm: true
    },

        function () {
            jQuery.ajax({
                url: $.MisUrls.url._EliminarMic_orga_panel_detalle + "?orga_panel_det_id=" + $orga_panel_det_id,
                type: "GET",
                dataType: "json",
                contentType: "application/json; charset=utf-8",
                success: function (data) {
                    if (data.resultado) {
                        _ObtenerMic_orga_panel_detalle($("#txtDet_id").val());
                    } else {
                        swal("Mensaje", "No se pudo eliminar el registro seleccionado", "warning")
                    }
                },
                error: function (error) {
                    console.log(error)
                },
                beforeSend: function () {

                },
            });
        });
}
