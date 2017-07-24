
if (typeof jQuery === 'undefined') {
  throw new Error('The Script requires jQuery')
}

function TMokaService(element, mokaModule, data, options){

    //has to create a new object for every instance

    this.$element = element; //html row element
    this.mokaModuleName = mokaModule;
    this.serviceName = data.name;
    this.options = options;
    this.parameter = data.parameter;
    this.functions = data.methods;
    this.state = data.state;

    this.createHtml = function(data){
        this.nameCol = $('<td></td>');
        this.stateCol = $('<td></td>');
        this.methodCol = $('<td></td>');
        this.htmlButtonGroup = $('<div class="btn-group text-center" role="group" aria-label="..."></div>');

        this.$element.append(this.nameCol.html(this.serviceName));
        this.$element.append(this.stateCol.html(this.state.split(".")[1]));
        this.$element.append(this.methodCol);

        this.methodCol.append(this.htmlButtonGroup);

        for(var i in this.functions){
            var methodName = this.functions[i].split(".")[1].toLowerCase();
            this.htmlButtonGroup.append('<a class="btn btn-primary" href="#" onclick="callServiceMethod( \''+this.mokaModuleName+'\',\''+this.serviceName+'\',\''+methodName+'\' )">'+methodName+'</a>');
        }
    }

    this.update = function(data){
        var htmlButtonGroupLabel = $('<div class="btn-group text-center" role="group" aria-label="..."></div>');
        this.functions=data.methods;
        this.state = data.state;

        this.stateCol.html(data.state.split(".")[1]);
        this.htmlButtonGroup.html('');
        for(var i in this.functions){
            var methodName = this.functions[i].split(".")[1].toLowerCase();
            this.htmlButtonGroup.append('<a class="btn btn-primary" href="#" onclick="callServiceMethod( \''+this.mokaModuleName+'\',\''+this.serviceName+'\',\''+methodName+'\' )">'+methodName+'</a>');
        }
    };

    this.createHtml(data);
}

function TMokaModule(element, data, options){

    this.$element = element;
    this.name = data.name;
    this.options = options;
    this.services = {};

    this.createHtml = function(data){
        this.title = $( '<h1></h1>');
        this.$element.append(this.title.html(data.name))

        table = $('<table class="table"><thead><tr><th>Dienst</th><th>Zustand</th><th>Methoden</th></tr></thead></table>');
        this.$element.append(table)
        this.tableBody = $('<tbody></tbody>');
        table.append(this.tableBody);

        for(key in data.services){
            row = $('<tr></tr>');
            this.tableBody.append(row);
            this.services[key] = new TMokaService(row, this.name, data.services[key]);
        }
    };

    this.update = function(data){
        for(key in data.services){
            this.services[key].update(data.services[key])
        }

    }

    this.createHtml(data);
}

function TMokaAnlage(element, data){
    this.modules = {};

    this.createHtml = function(data){
        for(key in data){
            div = $('<div class="MokaModule col-xs-6"></div>')
            div.appendTo(element);
            this.modules[key] = new TMokaModule(div, data[key]);

        }
    };

    this.update = function(data){
        for(key in data){
            this.modules[key].update(data[key])
        }
    };

    this.createHtml(data);
    this.$element = element;
}

function TRecipeService(element, data){

    this.$element = element;
    this.timeout = data.timeout;
    this.name = data.name;
    this.opcName = data.opcService.name;
    this.module = data.opcService.module;
    this.method = data.method.toLowerCase();
    this.serviceType = data.serviceType;
    this.state = data.state.split('.')[1];
    if(this.state == 'WAITING')
        panel = $('<div class="panel panel-info"></div>');
    else if(this.state == 'RUNNING')
        panel = $('<div class="panel panel-warning"></div>');
    else if(this.state == 'COMPLETED')
        panel = $('<div class="panel panel-success"></div>');
    else if(this.state == 'ABORTED')
        panel = $('<div class="panel panel-danger"></div>');
    else
        panel = $('<div class="panel panel-primary"></div>');

    this.$element.append(panel);
    this.head = $('<div class="panel-heading"></div>');
    this.body = $('<div class="panel-body"></div>');
    panel.append(this.head);
    panel.append(this.body);
    this.head.html(this.name+'<span class="badge adge-default badge-pill">'+this.state+'</span>');
    this.body.append($('<div class="col-xs-4"></div>').append('Modul: '+this.module));
    this.body.append($('<div class="col-xs-4"></div>').append('OPC-Dienst: '+this.opcName));
    this.body.append($('<div class="col-xs-4"></div>').append('Methode: '+this.method));
    this.body.append($('<div class="col-xs-4"></div>').append('Timeout: '+this.timeout));
    this.body.append($('<div class="col-xs-4"></div>').append('Stop-Bedingung: '+this.serviceType.complete.toString()));


}

function TRecipeBlock(element, data){
    this.$element = element;
    this.name = data.name;
    this.type = data.type;
    this.order = data.order;
    this.childs = {}
    for(i in this.order){
        child = data.childs[this.order[i]];
        div = ''
        if(this.type == 'SeriellerBlock'){
            div = $('<li class="list-group-item"></li>');
        }
        else {
            div = $('<td></td>');
        }
        this.$element.append(div);
        //Service Node
        if(!child.type){
            this.childs[i] = new TRecipeService(div, child);
        }
        else if(child.type == 'SeriellerBlock'){
            sNode = $('<ul class="list-group"></ul>');
            div.append(sNode);
            this.childs[i] = new TRecipeBlock(sNode, child);
        }
        else {
            pNode = $('<tr></tr>');
            tableBody = $('<tbody></tbody>');
            table = $('<table class="table table-bordered"></table>');
            table.append(tableBody)
            div.append(table);
            tableBody.append(pNode);
            this.childs[i] = new TRecipeBlock(pNode, child);
        }
    }

}
function TRecipe(element, data, options) {
    this.$element  = $(element);
    this.options   = options;
    this.author = data.instance.author;
    this.name = data.instance.name;
    this.date = data.instance.date;
    this.nameDiv = $('<div class="col-xs-4"></div>').append('Rezeptname: '+this.name);
    this.authorDiv = $('<div class="col-xs-4"></div>').append('Author: '+this.author);
    this.date = $('<div class="col-xs-4"></div>').append('Erstelldatum: '+this.author);

    ul = $('<ul class="list-group"></ul>');
    this.$element.append(ul);
    this.runBlock = new TRecipeBlock(ul, data.instance.runBlock);
}

function startRecipe(recipe){
    $.getJSON("/recipe/start/"+recipe+"/",
        function (data){
            $.toaster({'title': 'Rezeptstart',
                'message':'Das Rezept \''+recipe+'\' wurde gestartet.',
                'priority': 'success',
                'settings': {
                    'timeout' : 5000
                }
            });
    })
}

function parseRecipe(recipe){
    $.getJSON("/recipe/parse/"+recipe+"/",
        function (data){
            if(data.status == 'OK'){
                $.toaster({'title': 'Rezept',
                    'message':'Das Rezept ist valide.',
                    'priority': 'success',
                    'settings': {
                        'timeout' : 5000
                    }
                });
            }
            else {
                $.toaster({'title': 'Rezept',
                    'message': data.message,
                    'priority': 'danger',
                    'settings': {
                        'timeout' : 10000
                    }
                });
            }

    })
}

function callServiceMethod(module, service, method){
    $.getJSON("/module/"+module+"/call/"+service+"/"+method+"/",
        function(data) {
            $.toaster({'title': 'Serviceaufruf '+method,
                'message':'Der Service '+module+'.'+service+' konnte erfolgreich ausgeführt werden',
                'priority': 'success',
                'settings': {
                    'timeout' : 5000
                }
            });
    });
}
