semaphores = [];
function Semaphore(m){
	semaphores.push(this);
	this.maxvalue=m;
	this.value=0;
	this.handle=semaphores.length;
}
Semaphore.prototype.acquire=function(){
	this.state++;
	if (this.state>this.max){
		this.state--;
		return false;
	}
	return true;
}
Semaphore.prototype.release=function(){
	this.state--;
}
Semaphore.prototype.__enter__ = Semaphore.prototype.acquire;
Semaphore.prototype.__exit__ = Semaphore.prototype.release;
