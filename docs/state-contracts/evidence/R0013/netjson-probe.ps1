$cases = @('{"addons":[]}','{"addons":[],}','{/* comment */ "addons":[]}',"{'addons':[]}",'{addons:[]}','{"addons":[{"name":"Tabliss"}],"addons":[]}','[{"addons":[]}]')
$rows=@()
foreach($raw in $cases){
 $reader=$null
 try {
  $bytes=[Text.Encoding]::UTF8.GetBytes($raw)
  $reader=[Runtime.Serialization.Json.JsonReaderWriterFactory]::CreateJsonReader($bytes,[Xml.XmlDictionaryReaderQuotas]::Max)
  $doc=New-Object Xml.XmlDocument
  $doc.XmlResolver=$null
  $doc.Load($reader)
  $rows+= [pscustomobject]@{input=$raw;accepted=$true;xml=$doc.OuterXml}
 } catch { $rows+=[pscustomobject]@{input=$raw;accepted=$false;error=$_.Exception.Message} }
 finally { if($null -ne $reader){$reader.Close()} }
}
$rows|ConvertTo-Json -Depth 6
