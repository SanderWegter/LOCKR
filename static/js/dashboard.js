var activities = [
	"None",					//0
	"Manufacturing",		//1
	"Researching Tech",		//2
	"Researching TE",		//3
	"Researching ME",		//4
	"Copying",				//5
	"Duplicating",			//6
	"Invention",			//7
	"Reverse engineering"	//8
]

function getIndustry(){
	$.getJSON("/internal/industry/getAllJobs", function(data){
		jobs = data.jobs
		translations = data.translations
		bps = data.bps

		var d = new Date();
		var curTime = d.getTime()
		var offset = d.getTimezoneOffset() * 60 * 1000;

		$.each(jobs, function(k,v){
			var startTime = v.start_date - offset
			var endTime = v.end_date - offset
			var timeLeft = countDown(endTime)
			var table = "None"
			switch(v.activity_id){
				case 1:
					table = "Manu"
					break;
				case 2:
				case 3:
				case 4:
					table = "Res"
					break;
				case 5:
				case 6:
					table = "Copy"
					break;
				case 7:
				case 8:
					table = "Res"
					break;
				default:
					table = "None"
			}
			var bpobpc = ""
			if (v.activity_id == 1 && bps[v.blueprint_id] != undefined){
				console.log(bps[v.blueprint_id])
				if (bps[v.blueprint_id].type == -1 || bps[v.blueprint_id].type > 0){
					bpobpc = " - BPO"
				}
				else if (bps[v.blueprint_id].type == -2){
					bpobpc = " - BPC"
				}
			}
			$(".industry"+table+"List").append("\
								<tr>\
									<td><img src='https://image.eveonline.com/Type/"+v.blueprint_type_id+"_32.png'><br>"+translations[v.blueprint_type_id]+""+bpobpc+"</td>\
									<td><img src='https://image.eveonline.com/Character/"+v.installer_id+"_32.jpg'><br>"+translations[v.installer_id]+"</td>\
									<td>"+translations[v.location_id]+"</td>\
									<td>"+activities[v.activity_id]+"<br>Runs: "+v.runs+"/"+v.licensed_runs+"</td>\
									<td>"+convertDate(startTime)+"</td>\
									<td>"+convertDate(endTime)+"</td>\
									<td>"+timeLeft+" - "+v.status+"</td>\
								</tr>\
				")
		})
		jQuery.extend( jQuery.fn.dataTableExt.oSort, {
		    "num-html-pre": function ( a ) {
				var x = String(a).replace( /<[\s\S]*?>/g, "" ).replace(/Done/g,0).split(" - active")[0]
				if (x == 0) return x
		        y = (parseInt(x.split("H")[0]) * 60 * 60) + parseInt(x.split("H")[1].split("M")[0])
		        return parseFloat( y );
		    },
		 
		    "num-html-asc": function ( a, b ) {
		        return ((a < b) ? -1 : ((a > b) ? 1 : 0));
		    },
		 
		    "num-html-desc": function ( a, b ) {
		        return ((a < b) ? 1 : ((a > b) ? -1 : 0));
		    }
		} );

		$("#industryManuTable").DataTable({
            'paging': true,
            'pageLength': 25,
            'lengthChange': true,
            'searching': true,
            'ordering': true,
            'order': [[ 6, "asc" ]],
            'columnDefs': [
		       { type: 'num-html', targets: 6 }
		     ],
            'info': true,
            'autoWidth': true,
            'language': {
                'search': "_INPUT_",
                'searchPlaceholder': "Search..."
            }
		})
		$("#industryCopyTable").DataTable({
            'paging': true,
            'pageLength': 25,
            'lengthChange': true,
            'searching': true,
            'ordering': true,
            'order': [[ 6, "asc" ]],
            'columnDefs': [
		       { type: 'num-html', targets: 6 }
		     ],
            'info': true,
            'autoWidth': true,
            'language': {
                'search': "_INPUT_",
                'searchPlaceholder': "Search..."
            }
		})
		$("#industryResTable").DataTable({
            'paging': true,
            'pageLength': 25,
            'lengthChange': true,
            'searching': true,
            'ordering': true,
            'order': [[ 6, "asc" ]],
            'columnDefs': [
		       { type: 'num-html', targets: 6 }
		     ],
            'info': true,
            'autoWidth': true,
            'language': {
                'search': "_INPUT_",
                'searchPlaceholder': "Search..."
            }
        })
	})
}

function formatNumber(n, d){
	if(d){
		return n.toFixed(2).replace(/(\d)(?=(\d{3})+\.)/g, '$1,');
	}
	return n.toFixed().replace(/(\d)(?=(\d{3})+(,|$))/g, '$1,')
}

function convertDate(epoch) {
    var date = new Date(epoch)
    var year = date.getFullYear();
    var month = ('0' + (date.getMonth() + 1)).slice(-2);
    var day = ('0' + date.getDate()).slice(-2);
    var hours = ('0' + date.getHours()).slice(-2);
    var minutes = ('0' + date.getMinutes()).slice(-2);
    var seconds = ('0' + date.getSeconds()).slice(-2);
    return year + "-" + month + "-" + day + " " + hours + ":" + minutes + ":" + seconds
}

function countDown(epoch){
	var cur = (new Date).getTime()
	var diff = epoch - cur
	if (diff < 0){
		return "Done"
	}
	var milliseconds = parseInt((diff%1000)/100)
            , seconds = parseInt((diff/1000)%60)
            , minutes = parseInt((diff/(1000*60))%60)
            , hours = parseInt((diff/(1000*60*60)));

        hours = (hours < 10) ? "0" + hours : hours;
        minutes = (minutes < 10) ? "0" + minutes : minutes;
        seconds = (seconds < 10) ? "0" + seconds : seconds;

        return hours + "H " + minutes + "M"
}

$(document).ready(function(){
	getIndustry()
})