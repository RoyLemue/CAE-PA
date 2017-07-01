
if (typeof jQuery === 'undefined') {
  throw new Error('The Script requires jQuery')
}

var MokaService = function(element, mokaModule, serviceName, options){
    this.$element = $(element); //html row element
    this.mokaModule = mokaModule;
    this.serviceName = serviceName;
    this.options = options;
    this.parameter = Array();
    this.functions = Array();
    this.state = 'OpcState.IDLE';
    var self = this;

    this.jsonStateFunction = function(data) {
                var stateCol, methodCol, buttonGroup;
                stateCol = self.$element.children().first().next();
                methodCol = self.$element.children().first().next().next();
                buttonGroup = methodCol.children().first();
                console.log(self);
                console.log(this);
                if (data.status == 'OK'){
                    self.functions = data.methods;
                    self.state = data.state;
                    stateCol.html(data.state);
                    buttonGroup.html('<div class="btn-group text-center" role="group" aria-label="...">');
                    data.methods.forEach(function(method, index){
                        buttonGroup.append('<a class="btn btn-primary" href="#" onclick="callServiceMethod( \''+self.mokaModule.name+'\',\''+self.serviceName+'\',\''+method+'\' )">'+method+'</a>');
                    });


                }
        };

    this.getState = function(){
        adress = "/module/"+this.mokaModule.name+"/getstate/"+this.serviceName+"/";
        $.getJSON(adress, this.jsonStateFunction);
    };
}

MokaService.prototype.updateState = function(){
    this.getState();
    //this.$element.children().first().next().html(this.state);
};

MokaService.prototype.callMethod = function(){
    $.getJSON(
        "/gntm/ajax/?model="+model+"&aktien="+aktien,
        function(data) {
          textField.html(data.price.summe.toFixed(2)+' {{currency | safe }}');
    });
    return state;
};


var MokaModule = function(element, name, options){
    this.$element = $(element);
    this.name = name;
    this.options = options;
    this.services = Array();
}


var RecipeElement = function (element, name, options) {
    this.$element  = $(element)
    this.options   = options
    this.isLoading = false
    this.name = name
}


RecipeElement.prototype.start = function () {
    $.getJSON("/recipe/start/"+recipe+"/",
        function(data) {
          this.$element.html('Working')
    });
}

RecipeElement.prototype.pause = function () {
    $.getJSON("/recipe/pause/"+recipe+"/",
        function(data) {
          this.$element.html('Paused');
    });
}

RecipeElement.prototype.stop =function () {
    $.getJSON("/recipe/stop/"+recipe+"/",
        function(data) {
          this.$element.html('Stopped')
    });
}

function callServiceMethod(module, service, method){
    $.getJSON("/module/"+module+"/call/"+service+"/"+method+"/",
        function(data) {

    });
}

