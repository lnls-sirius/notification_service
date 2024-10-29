

function selectRule(e){
    contentDiv = e.parentElement.parentElement.parentElement;
    var elemRule = contentDiv.children[1].children[1].children[0];
    var limitSimple = contentDiv.children[2];
    var limitComposite = contentDiv.children[3];
    var elemLimit = contentDiv.children[2].children[1].children[0];
    var elemLimitLL = contentDiv.children[3].children[1].children[0];
    var elemLimitLU = contentDiv.children[3].children[3].children[0];
    // var oldLimitValue = $('#limit').data('old');
    // var oldLimitLLValue = $('#limitLL').data('old');
    // var oldLimitLUValue = $('#limitLU').data('old');
    var strRule = e.options[e.selectedIndex].text;
    if (elemLimitLL.value = null) {
        elemLimitLL.value = '';}
    if (elemLimitLU.value = null) {
        elemLimitLU.value = '';}
    if(strRule.includes('LL')){
        elemLimit.value = '';
        elemLimit.setAttribute('show', 'off');
        limitSimple.style.visibility = "hidden";
        limitSimple.style.display = "none";
        elemLimitLL.setAttribute('show', 'on');
        elemLimitLU.setAttribute('show', 'on');
        limitComposite.style.visibility = "visible";
        limitComposite.style.display = "";
        // elemLimitLU.value = oldLimitLUValue || '';
        // elemLimitLL.value = oldLimitLLValue || '';
        elemLimitLU.hidden=false;
        elemLimitLL.hidden=false;
        elemLimit.hidden=true;
        }
    else {
        elemLimitLU.value = '';
        elemLimitLL.value = '';
        elemLimit.setAttribute('show', 'on');
        limitSimple.style.visibility = "visible";
        limitSimple.style.display = "";
        elemLimitLL.setAttribute('show', 'off');
        elemLimitLU.setAttribute('show', 'off');
        limitComposite.style.visibility = "hidden";
        limitComposite.style.display = "none";
        // elemLimit.value = oldLimitValue || '';
        elemLimitLU.hidden=true;
        elemLimitLL.hidden=true;
        elemLimit.hidden=false;
        }
    }

function cloneDiv(parentDiv, activeCoreIndex=0){
    var clonedDiv = parentDiv.cloneNode(true);
    contentDiv = parentDiv.parentElement;
    var array_cores = []; //array of notificationCores indexes
    var currentCores = Array.from(contentDiv.children); //array of notificationCores
    for (var i = 0; i <= currentCores.length-1; i++){
        array_cores.push(Number(currentCores[i].id.slice(16))); }
    var max_value = Math.max(...array_cores)
    var missing = []; //array of missing notificationCores indexes
    for (var i = 0; i <= max_value; i++) {
        if (array_cores.indexOf(i) == -1) {
            missing.push(i);}
    }
    data_cloned = "true";
    if (missing.length !== 0) {
        clonedDiv.id = "notificationCore" + Math.min(...missing).toString();
    }
    else {
        clonedDiv.id = "notificationCore" + (max_value + 1).toString();
    }
    clonedDivChild = clonedDiv.children;
    clonedDivChild = clonedDivChild[0].children[0];
    clonedDivChild.id = "contentDiv" + (max_value + 1).toString();
    closeOn = clonedDivChild.getAttribute('data-close');
    if (closeOn == "false"){
        clonedDivChild.innerHTML += (
            ("<div style='margin-left:auto;margin-right:10px;margin-top:5px;' data-father='none'>"+
                "<button class='close' type='button' aria-label='Close'>"+
                    "<span aria-hidden='true' onClick='closeDiv(this)' id='buttonCloseSpan'>×</span>"+
                "</button>"+
            "</div>"));
            }
    var container = document.getElementById("container");
    parentDiv.setAttribute("data-cloned", "true");
    clonedDivChild.setAttribute("data-close", "true");
    att_data_caller = clonedDivChild.parentElement.parentElement;
    att_data_caller.setAttribute("data-caller", (activeCoreIndex).toString());
    clonedDivChild.children[5].setAttribute('data-father', activeCoreIndex.toString());
    var pv = clonedDivChild.children[0].children[1].children[0];
    clonedDivChild.children[0].children[1].children[0].value = '';
    var rule = clonedDivChild.children[1].children[1].children[0];
    clonedDivChild.children[1].children[1].children[0].value = '';
    var limit = clonedDivChild.children[2].children[1].children[0];
    clonedDivChild.children[2].children[1].children[0].value = '';
    var limitLL = clonedDivChild.children[3].children[1].children[0];
    clonedDivChild.children[3].children[1].children[0].value = '';
    var limitLU = clonedDivChild.children[3].children[3].children[0];
    clonedDivChild.children[3].children[3].children[0].value = '';
    var subrule = clonedDivChild.children[4].children[1].children[0];
    clonedDivChild.children[4].children[1].children[0].value = '';
    pv.setAttribute('id', 'pv' + (Number(activeCoreIndex) + 1).toString());
    pv.setAttribute('name', 'pv' + (Number(activeCoreIndex) + 1).toString())
    rule.setAttribute('id', 'rule' + (Number(activeCoreIndex) + 1).toString());
    rule.setAttribute('name', 'rule' + (Number(activeCoreIndex) + 1).toString());
    limit.setAttribute('id', 'limit' + (Number(activeCoreIndex) + 1).toString());
    limit.setAttribute('name', 'limit' + (Number(activeCoreIndex) + 1).toString());
    limit.setAttribute('title', '');
    limitLL.setAttribute('id', 'limitLL' + (Number(activeCoreIndex) + 1).toString());
    limitLL.setAttribute('name', 'limitLL' + (Number(activeCoreIndex) + 1).toString());
    limitLL.setAttribute('title', '');
    limitLU.setAttribute('id', 'limitLU' + (Number(activeCoreIndex) + 1).toString());
    limitLU.setAttribute('name', 'limitLU' + (Number(activeCoreIndex) + 1).toString());
    limitLU.setAttribute('title', '');
    subrule.setAttribute('id', 'subrule' + (Number(activeCoreIndex) + 1).toString());
    subrule.setAttribute('name', 'subrule' + (Number(activeCoreIndex) + 1).toString());
    container.appendChild(clonedDiv);
}

function changeSubrule(e){
    var parentDiv = e.parentElement;
    activeCore = parentDiv.parentElement.parentElement.parentElement.parentElement;
    activeCoreIndex = activeCore.id.slice(16);
    while(parentDiv.id.indexOf('notificationCore') == -1){
        parentDiv = parentDiv.parentElement;}
    data_cloned = parentDiv.getAttribute('data-cloned');
    data_close = parentDiv.chidren;
    if (e.value == 'AND' || e.value =='OR' || e.value == 'NOT'){
        if (data_cloned == "false"){
            cloneDiv(parentDiv, activeCoreIndex)
        }
    }
}

function gethint(e){
    var aux = (e.id).split('limit')[1]
    var elem = "[id^='pv" + aux + "']"
    $.ajax({
        type: "GET",
        url: "/ns/gethint",
        data: {pv: $(elem).val()},
        success: function(data) {
            if (data == 'None') {
                $('[id^="limit"]').tooltip({ items: ':not(.menu)' })}
            else {
                $('[id^=limit' + aux + "]").attr('title', data)};
            }
        });
    }

function autocomplete(e){
    $(e).autocomplete({
        source:function(request,response){
            $.getJSON("{{url_for('autocomplete')}}",{
                q: request.term, // in flask, "q" will be the argument to look for using request.args
                },
            function(data) {
                response(data.matching_results.slice(0,500)); // matching_results from jsonify
                    }
                );
            }
        })
    }

function closeDiv(e){
    parentDivButton = e.parentElement;
    parentDivDiv = parentDivButton.parentElement; //actual x button div
    contentDiv = parentDivDiv.parentElement;
    midDiv = contentDiv.parentElement;
    notificationCore = midDiv.parentElement;
    container = notificationCore.parentElement;
    var currentCores = Array.from(container.children);
    var divToClose = 'none';
    var aux = Array.from(container.children); //array of notificationCores
    var containerCores = []
    for (var i = 0; i <= aux.length - 1; i++){
        containerCores.push(aux[i].id.slice(16));
        }
    caller = notificationCore.getAttribute('data-caller');
    if (containerCores.indexOf(caller) != -1){
        notificationCore.remove();
        coreOld = document.querySelector("#" + "notificationCore" + caller.toString());
        coreOldSubrule = coreOld.children[0].children[0].children[4].children[1].children[0];
        coreOldSubrule[0].selected = 'selected';
        coreOld.setAttribute("data-cloned", "false");
        }
        else {
            notificationCore.remove();
        }
    }

function getDateTime() {
    var now     = new Date();
    var year    = now.getFullYear();
    var month   = now.getMonth()+1;
    var day     = now.getDate();
    var hour    = now.getHours();
    var minute  = now.getMinutes();
    var second  = now.getSeconds();
    if(month.toString().length == 1) {
            month = '0'+month;
    }
    if(day.toString().length == 1) {
            day = '0'+day;
    }
    if(hour.toString().length == 1) {
            hour = '0'+hour;
    }
    if(minute.toString().length == 1) {
            minute = '0'+minute;
    }
    if(second.toString().length == 1) {
            second = '0'+second;
    }
    var dateTime = year+'-'+month+'-'+day+' '+hour+':'+minute;
        return dateTime;
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function submitForm(e, op, id=NaN){
    var form = e.parentElement.parentElement; //form
    var container = form.children[0];
    var notification = {
        created: {},
        expiration: {},
        interval: {},
        persistence: {},
        notificationCores: {}
        };
    var notificationJSON = [];
    for (var i = 0; i < container.children.length; i++){
        var expiration = form.parentElement.children[0].children[1].children[0];
        var interval = form.parentElement.children[0].children[5].children[0];
        var persistence = form.parentElement.children[0].children[7].children[0];
        var sms_text = form.parentElement.children[0].children[10].children[0];
        var notificationCore = container.children[i];
        var fields = notificationCore.querySelectorAll("input[show='on'],select");
        // console.log(fields)
        // console.log(sms_text)
        var jsonObj = {notification: {}}
        for (var j = 0; j < fields.length; j++){
            var field = fields[j].id;
            jsonObj.notification[field] = fields[j].value;
        }
        // console.log(jsonObj.notification);
        // await sleep(15000);
        notificationCoreId = notificationCore.id;
        jsonObj[notificationCoreId] = jsonObj["notification"];
        delete jsonObj["notification"];
        notificationJSON.push(jsonObj);
    }
    var today = new Date();
    var date = today.getFullYear()+'-'+(today.getMonth()+1)+'-'+today.getDate();
    var time = today.getHours() + ":" + today.getMinutes();
    currentTime = getDateTime();
    notification["created"] = currentTime;
    notification["expiration"] = expiration.value;
    notification["interval"] = interval.value;
    notification["persistence"] = persistence.value;
    notification["sms_text"] = sms_text.value;
    notification["notificationCores"] = notificationJSON;
    nclen = notification["notificationCores"].length
    // console.log(sms_text)
    // await sleep(5000);
    var formData = JSON.stringify(notification);
    var xhr = new XMLHttpRequest();
    sessionStorage.setItem("expiration", $('#datetimepicker5').val());
    var expiration = sessionStorage.getItem("expiration");
    sessionStorage.setItem("interval", $('#interval').val());
    var interval = sessionStorage.getItem("interval");
    sessionStorage.setItem("persistence", $('#persistence').val());
    var persistence = sessionStorage.getItem("persistence");
    sessionStorage.setItem("sms_text", $('#sms_text').val());
    var sms_text = sessionStorage.getItem("sms_text");
    sessionStorage.setItem("pv", $('#pv').val());
    var pv = sessionStorage.getItem("pv");
    sessionStorage.setItem("rule", $('#rule').val());
    var rule = sessionStorage.getItem("rule");
    sessionStorage.setItem("limit", $('#limit').val());
    var limit = sessionStorage.getItem("limit");
    sessionStorage.setItem("limitLL", $('#limitLL').val());
    var limitLL = sessionStorage.getItem("limitLL");
    sessionStorage.setItem("limitLU", $('#limitLU').val());
    var limitLU = sessionStorage.getItem("limitLU");
    sessionStorage.setItem("subrule", $('#subrule').val());
    var subrule = sessionStorage.getItem("subrule");
    sessionStorage.setItem('reload', 'true')
    if (op == 'add'){
        xhr.open("POST", "/ns/notifications/add", true);
        xhr.send(formData);
        xhr.onload = function() {
            if (xhr.status == 200){
                window.location.href = "/ns/notifications"; }
            else {
                // window.location.reload();
                $('#alert-top').load(xhr.responseURL + ' #alert-top');
                $(document).ready(function() {
                    setTimeout(function() {
                        $('#alert').fadeOut('fast');
                    }, 6000); // <-- time in milliseconds
                    });
                // document.getElementById("datetimepicker5").setAttribute('value', expiration);
                // document.getElementById("interval").value = interval;
                // document.getElementById("persistence").value = persistence;
                // document.getElementById("sms_text").value = sms_text;
                // document.getElementById("pv0").value = pv;
                // document.getElementById("rule0").value = rule;
                // document.getElementById("limit0").value = limit;
                // document.getElementById("limitLL0").value = limitLL;
                // document.getElementById("limitLU0").value = limitLU;
                // document.getElementById("subrule0").value = subrule;
                }
            }
        }
    else if (op == 'edit'){
        xhr.open("POST", "/ns/notifications/edit/"+id, true);
        xhr.setRequestHeader('notification_id', id);
        xhr.send(formData);
        // console.log(formData);
        // await sleep(5000);
        xhr.onload = function() {
        if (xhr.status == 200){
            window.location.href = "/ns/notifications"; }
        else {
            $('#alert-top').load(xhr.responseURL + ' #alert-top');
            $(document).ready(function() {
                setTimeout(function() {
                    $('#alert').fadeOut('fast');
                }, 5000); // <-- time in milliseconds
                });
            // window.location.reload();
            // document.getElementById("datetimepicker5").setAttribute('value', expiration);
            // document.getElementById("interval").value = interval;
            // document.getElementById("persistence").value = persistence;
            // document.getElementById("sms_text").value = sms_text;
            // document.getElementById("pv0").value = pv;
            // document.getElementById("rule0").value = rule;
            // document.getElementById("limit0").value = limit;
            // document.getElementById("limitLL0").value = limitLL;
            // document.getElementById("limitLU0").value = limitLU;
            // document.getElementById("subrule0").value = subrule; }
            }
        }
    }
    else {
        xhr.open("POST", "/ns/notifications/cancel", true);
        xhr.send(formData);
        xhr.onload = function() {
        if (xhr.status == 200){
            window.location.href = "/ns/notifications"; }
        }
    }
}

function toJson(vars){
    obj = JSON.parse(vars.replaceAll('&#34;', '\"').replaceAll('&lt;', '<').replaceAll('&gt;', '>').replaceAll('&#39;', "'"));
    return obj;
}

function JsonToForm(data){
    for(key in data){
        if(data.hasOwnProperty(key))
            $('[name='+key+']').val(data[key]);
        }
    }
